# local_serial_control2.py
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import asyncio
import websockets
import json
import pygame
import serial.tools.list_ports as ports
import serial
import time
import threading
import queue
import sys

# --- Helpers ---
def find_pico_port():
    pico_ports = [p for p in ports.comports() if ('ACM' in p.device or 'USB' in p.device)]
    return pico_ports[0].device if pico_ports else None

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# --- Serial setup ---
SERIAL_PORT = find_pico_port()
BAUD_RATE = 115200

if SERIAL_PORT is None:
    print("No Pico serial port found. Exiting.")
    sys.exit(1)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05, write_timeout=0.05)
    print(f"Opened serial {SERIAL_PORT} @ {BAUD_RATE}")
except serial.SerialException as e:
    print("Serial error:", e)
    sys.exit(1)

# --- Control arbitration & globals ---
control_mode = 'remote'         # 'local' or 'remote'
last_local_input_time = time.time()
LOCAL_TIMEOUT_SECONDS = 5.0

serial_queue = queue.Queue()
MAX_SPEED = 100

# --- Serial sender thread ---
def serial_sender():
    while True:
        try:
            cmd = serial_queue.get(timeout=0.1)
            if ser and ser.is_open:
                try:
                    ser.write(cmd.encode('utf-8'))
                except Exception as e:
                    print("Serial write error:", e)
                serial_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print("Serial sender exception:", e)
            time.sleep(0.1)

threading.Thread(target=serial_sender, daemon=True).start()

# --- Controller helpers (make trigger reading robust) ---
def read_triggers(joystick):
    """
    Returns (lt, rt) each in range 0..1
    Tries axis mapping first (common: axis 2 = LT, axis 5 = RT)
    Falls back to button indices commonly used for triggers if axes not present.
    """
    lt = 0.0
    rt = 0.0
    try:
        # try axis mapping (some controllers map triggers -1..1)
        # common mapping: axis 2 = LT, axis 5 = RT (range -1..1)
        axes = joystick.get_numaxes()
        if axes > 2:
            # safe-get with try/except
            try:
                raw_lt = joystick.get_axis(2)
                lt = (raw_lt + 1.0) / 2.0  # convert -1..1 -> 0..1
            except Exception:
                lt = 0.0
        if axes > 5:
            try:
                raw_rt = joystick.get_axis(5)
                rt = (raw_rt + 1.0) / 2.0
            except Exception:
                rt = 0.0

        # If both zero, try reading as button-style (some controllers)
        if lt == 0.0 and rt == 0.0:
            btns = joystick.get_numbuttons()
            # common button indices for triggers in some mappings:
            # left trigger button index 6, right trigger index 7 (this varies)
            if btns > 6:
                try:
                    lt = 1.0 if joystick.get_button(6) else 0.0
                except Exception:
                    lt = 0.0
            if btns > 7:
                try:
                    rt = 1.0 if joystick.get_button(7) else 0.0
                except Exception:
                    rt = 0.0

    except Exception:
        lt = 0.0; rt = 0.0

    # clamp
    lt = clamp(lt, 0.0, 1.0)
    rt = clamp(rt, 0.0, 1.0)
    return lt, rt

# --- Local controller thread (mecanum mixing) ---
def local_controller_thread():
    global control_mode, last_local_input_time
    pygame.init()
    pygame.joystick.init()

    joystick = None
    prev_out = (0,0,0,0)  # FL,FR,RL,RR

    while True:
        pygame.event.pump()

        # detect joystick connection
        if joystick is None and pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            control_mode = 'local'
            print("Local controller connected; switching to LOCAL mode.")

        if joystick is None:
            time.sleep(0.05)
            continue

        # Read forward/back (left stick Y), rotation (right stick X)
        try:
            forward = joystick.get_axis(1)   # invert: up => +1
        except Exception:
            forward = 0.0
        try:
            rotate = joystick.get_axis(3)     # right stick X
        except Exception:
            rotate = 0.0

        # Triggers -> strafe
        lt, rt = read_triggers(joystick)
        strafe = rt - lt   # RT = +1 => strafe right; LT = +1 => strafe left

        # Deadzone
        def dz(v, th=0.05):
            return 0.0 if abs(v) < th else v
        forward = dz(forward); rotate = dz(rotate); strafe = dz(strafe)

        # Update last activity time if any movement
        if abs(forward) > 0.01 or abs(rotate) > 0.01 or abs(strafe) > 0.01:
            last_local_input_time = time.time()

        # Mecanum mixing (unnormalized)
        fl = -forward + strafe + rotate
        fr = -forward - strafe - rotate
        rl = forward - strafe + rotate
        rr = forward + strafe - rotate

        # Normalize if needed
        max_mag = max(abs(fl), abs(fr), abs(rl), abs(rr), 1.0)
        fl /= max_mag; fr /= max_mag; rl /= max_mag; rr /= max_mag

        # Scale to integer -100..100
        out = (int(round(fl * MAX_SPEED)),
               int(round(fr * MAX_SPEED)),
               int(round(rl * MAX_SPEED)),
               int(round(rr * MAX_SPEED)))

        # Send if changed (and we are local)
        if control_mode == 'local' and out != prev_out:
            cmd = f"M{out[0]},{out[1]},{out[2]},{out[3]}\n"
            serial_queue.put(cmd)
            prev_out = out

        # Timeout -> switch back to remote and stop motors
        if time.time() - last_local_input_time > LOCAL_TIMEOUT_SECONDS:
            if control_mode == 'local':
                print("Local controller idle; switching to REMOTE and stopping motors.")
                control_mode = 'remote'
                serial_queue.put("M0,0,0,0\n")

        # Detect unplug
        if pygame.joystick.get_count() == 0:
            if joystick is not None:
                print("Local controller unplugged; reverting to REMOTE and stopping motors.")
                joystick = None
                control_mode = 'remote'
                serial_queue.put("M0,0,0,0\n")

        time.sleep(0.02)  # 50 Hz

threading.Thread(target=local_controller_thread, daemon=True).start()

# --- WebSocket handler (remote control) ---
async def message_process(websocket):
    global control_mode
    print("WebSocket client connected.")
    prev_out = (0,0,0,0)

    try:
        async for message in websocket:
            data = json.loads(message)

            if not data.get("connection_status", False):
                continue

            # Map remote fields same as local mapping:
            forward = -data.get("left_stick_y", 0.0)   # invert so up=+1
            rotate  = data.get("right_stick_x", 0.0)

            # Read triggers from JSON if present (HTML sends triggers in buttons or fields)
            # Try common fields:
            lt = data.get("trigger_left", None)
            rt = data.get("trigger_right", None)

            # HTML joystick earlier sent triggers as 0..65535, so if present scale to 0..1
            if lt is not None:
                try:
                    lt = float(lt) / 65535.0
                except Exception:
                    lt = 0.0
            else:
                lt = 0.0

            if rt is not None:
                try:
                    rt = float(rt) / 65535.0
                except Exception:
                    rt = 0.0
            else:
                rt = 0.0

            # If triggers not present, fallback to left-right on dpad or zero
            strafe = rt - lt

            # Deadzone
            def dz(v, th=0.05):
                return 0.0 if abs(v) < th else v
            forward = dz(forward); rotate = dz(rotate); strafe = dz(strafe)

            # Mecanum mixing
            fl = forward + strafe + rotate
            fr = forward - strafe - rotate
            rl = forward - strafe + rotate
            rr = forward + strafe - rotate

            max_mag = max(abs(fl), abs(fr), abs(rl), abs(rr), 1.0)
            fl /= max_mag; fr /= max_mag; rl /= max_mag; rr /= max_mag

            out = (int(round(fl * MAX_SPEED)),
                   int(round(fr * MAX_SPEED)),
                   int(round(rl * MAX_SPEED)),
                   int(round(rr * MAX_SPEED)))

            if control_mode == 'remote' and out != prev_out:
                cmd = f"M{out[0]},{out[1]},{out[2]},{out[3]}\n"
                serial_queue.put(cmd)
                prev_out = out

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket client disconnected.")
    except Exception as e:
        print("WebSocket error:", e)

# --- WebSocket server ---
async def main():
    async with websockets.serve(message_process, "0.0.0.0", 5000):
        print("WebSocket server listening on ws://0.0.0.0:5000")
        print("Control mode:", control_mode)
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        try:
            ser.close()
        except:
            pass
        pygame.quit()
