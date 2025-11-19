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

# Function to find the Pico Serial port dynamically
def find_pico_port():
    pico_ports = [port for port in ports.comports() if 'ACM' in port.device or 'USB' in port.device]
    if pico_ports:
            return pico_ports[0].device # Return the first found port
    return None

# --- Configuration ---
#Set up serial communication with the Pico (adjust port and baud rate)
SERIAL_PORT = find_pico_port()
BAUD_RATE = 9600
try:
    # Use queue for thread-safe serial communication
    ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=0.1,
    write_timeout=0.1
    )
    print(f"Serial port {SERIAL_PORT} opened successfully.")
except serial.SerialException as e:
    print(f"Serial port error: {e}")
    sys.exit(1)
    
    
# Global variable to manage control priority
# 'remote' is the default mode
# 'local' takes over if the Bluetooth controller is connected and active
control_mode = 'remote'
last_local_input_time = time.time()
LOCAL_TIMEOUT_SECONDS = 5 # Timeout for local control inactivity

# A dictionary to hold the current desired robot state (e.g., motor speed, light status)
#This gets populated by either the websocket or the local controller
robot_state = {
    'left_motor_speed': 0,
    'right_motor_speed': 0,
    'light_on': False,
}

# Queue for sending commands from the threads to the main serial port handler
serial_queue = queue.Queue()


# --- Serial Sender Thread Function ---
def serial_sender():
    """Reads commands from the queue and sends them to the Pico."""
    while True:
        try:
            command = serial_queue.get(timeout=0.1) # Wait briefly for a command 
            
            if ser and ser.is_open:
                ser.write(command.encode('utf-8'))
                serial_queue.task_done()
                #print(f"[SERIAL TX] Sent Command: {command.strip()}")
        except queue.Empty:
            continue
        except serial.SerialException as e:
            print(f"Serial port exception during send: {e}")
            time.sleep(0.1)    
        except Exception as e:
            print(f"Error sending serial data: {e}")
            time.sleep(0.1)
        
# Start the serial sender thread
serial_thread = threading.Thread(target=serial_sender, daemon=True)
serial_thread.start()
#ser.write(b'\x04')

left_motor_val = 0
right_motor_val = 0
MAX_SPEED = 100

# --- Local Controller (Pygame) Thread Function ---
def check_local_controller():
    global control_mode, last_local_input_time, left_motor_val, right_motor_val
    
    pygame.init()
    pygame.joystick.init()
    joystick = None

    prev_left = 0
    prev_right = 0

    while True:
        # Must call event pump
        pygame.event.pump()

        # Detect controller
        if joystick is None and pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print("Local controller connected. Switching to LOCAL control.")
            control_mode = "local"

        # No controller plugged in
        if joystick is None:
            time.sleep(0.1)
            continue

        # Read joystick axes
        forward_speed = -joystick.get_axis(1)   # Left stick Y
        steer_speed   =  joystick.get_axis(3)   # Right stick X

        # Detect ANY activity
        if abs(forward_speed) > 0.05 or abs(steer_speed) > 0.05:
            last_local_input_time = time.time()

        # Skid steering mix
        forward_val = int(forward_speed * MAX_SPEED)
        steer_val   = int(steer_speed   * MAX_SPEED)

        left_motor_val  = max(-MAX_SPEED, min(MAX_SPEED, forward_val - steer_val))
        right_motor_val = max(-MAX_SPEED, min(MAX_SPEED, forward_val + steer_val))

        # Only send if changed
        if (left_motor_val != prev_left) or (right_motor_val != prev_right):
            serial_queue.put(f"L{left_motor_val}R{right_motor_val}\n")
            prev_left = left_motor_val
            prev_right = right_motor_val

        # Idle timeout
        if time.time() - last_local_input_time > LOCAL_TIMEOUT_SECONDS:
            if control_mode == "local":
                print("Local timeout → Switching to REMOTE")
                control_mode = "remote"
                serial_queue.put("L0R0\n")

        # Detect unplug
        if pygame.joystick.get_count() == 0:
            print("Controller unplugged → REMOTE mode")
            joystick = None
            control_mode = "remote"
            serial_queue.put("L0R0\n")

        time.sleep(0.02)
        
# Start the local controller thread
controller_thread = threading.Thread(target=check_local_controller, daemon=True)
controller_thread.start()


# --- WebSocket Server Functions (Your existing code + arbitration) ---

async def message_process(websocket):
    global control_mode

    print("WebSocket client connected.")

    # Previous motor values (to avoid sending duplicates)
    prev_left = 0
    prev_right = 0

    try:
        async for message in websocket:
            data = json.loads(message)

            # Ignore if no controller data
            if not data.get("connection_status", False):
                continue

            # Pull axes from JSON
            forward_axis = data.get("left_stick_y", 0)   # forward/back
            steer_axis   = data.get("right_stick_x", 0)  # left/right

            # Invert forward axis so up = forward
            forward_val = int(-forward_axis * MAX_SPEED)
            steer_val   = int( steer_axis * MAX_SPEED)

            # Skid-steer mix
            left_val  = max(-MAX_SPEED, min(MAX_SPEED, forward_val + steer_val))
            right_val = max(-MAX_SPEED, min(MAX_SPEED, forward_val - steer_val))

            # Only act if remote control has priority
            if control_mode == "remote":

                # Only send command if changed to avoid flooding serial
                if left_val != prev_left or right_val != prev_right:
                    cmd = f"L{left_val}R{right_val}\n"
                    serial_queue.put(cmd)

                    prev_left = left_val
                    prev_right = right_val

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
        
async def main():
    # Use the single-argument handler required by your installed library version
    async with websockets.serve(message_process, "0.0.0.0", 5000):
        print("WebSocket server started at ws://0.0.0.0:5000")
        print(f"Current Control Mode: {control_mode}") 
        await asyncio.Future() # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program shutting down.")
    finally:
        ser.close()
        pygame.quit()

