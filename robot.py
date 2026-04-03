import json
import time
import websocket
import threading
import signal
import serial
import struct
import os
import base64

import cv2
import numpy as np

SERVER_URL = "ws://192.168.1.123:1909"

ROBOT_SENDER      = "3"   # robot control sender id
CONTROLLER_SENDER = "1"   # controller client id
CAM_SENDER        = "3_cam"
CAM_DESTINATION   = "4"   # UI / operator client id for video

DEADZONE   = 0.05
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200
UPDATE_HZ   = 50.0

# Camera config
CAM_DEVICE_INDEX = 0          # /dev/video0
CAM_WIDTH        = 640
CAM_HEIGHT       = 360
CAM_FPS          = 10.0       # desired send rate

# ---------- Preset positions (0.0-1.0 normalized) ----------
ARM_BASE_STOW   = 0.2
ARM_BASE_PICK   = 0.5
ARM_BASE_DROP_1 = 0.6
ARM_BASE_DROP_2 = 0.7
ARM_BASE_DROP_3 = 0.8
ARM_BASE_DROP_4 = 0.9

WRIST_STOW   = 0.2
WRIST_PICK   = 0.7
WRIST_DROP   = 0.5

CLAW_OPEN    = 0.2
CLAW_CLOSED  = 0.8

CLIMB_STOW   = 0.0
CLIMB_HOOK   = 0.5
CLIMB_UP     = 1.0

# ---------- Helpers ----------
def clamp(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))

def apply_deadzone(v, dz=DEADZONE):
    return 0.0 if abs(v) < dz else v

def normalize_wheels(wheels):
    m = max(abs(w) for w in wheels)
    return [w / m for w in wheels] if m > 1.0 else wheels

def mecanum_blend(left_x, left_y, trig_l, trig_r):
    vx = clamp(apply_deadzone(left_y))               # forward/back
    vy = clamp(apply_deadzone(trig_r - trig_l))      # strafe right-left
    omega = clamp(apply_deadzone(left_x))            # turn

    fl = vx + vy + omega
    fr = vx - vy - omega
    bl = vx - vy + omega
    br = vx + vy - omega
    return normalize_wheels([fl, fr, bl, br])

# ---------- Robot command struct (Pi -> Pico) ----------
def float_to_int16(v):
    v = clamp(v, -1.0, 1.0)
    return int(v * 32767)

def norm01_to_u16(v):
    v = max(0.0, min(1.0, v))
    return int(v * 65535)

def default_robot_command():
    return {
        "drive": [0.0, 0.0, 0.0, 0.0],
        "intake_power": 0.0,
        "arm_base_pos": ARM_BASE_STOW,
        "wrist_pos": WRIST_STOW,
        "claw_pos": CLAW_OPEN,
        "climb_pos": CLIMB_STOW,
        "arm_extend_power": 0.0,
        "voltage_device_on": False,
        "wheel_rpm_target": 0
    }

def pack_robot_command(cmd):
    drive_fl, drive_fr, drive_bl, drive_br = cmd["drive"]
    intake_power = cmd["intake_power"]
    arm_base_pos = cmd["arm_base_pos"]
    wrist_pos    = cmd["wrist_pos"]
    claw_pos     = cmd["claw_pos"]
    climb_pos    = cmd["climb_pos"]
    arm_extend_power = cmd["arm_extend_power"]
    voltage_on   = cmd["voltage_device_on"]
    wheel_rpm    = cmd["wheel_rpm_target"]

    flags = 0
    if voltage_on:
        flags |= 0x01

    # Layout: <5h5HBBH
    data = struct.pack(
        "<5h5HBBH",
        float_to_int16(drive_fl),
        float_to_int16(drive_fr),
        float_to_int16(drive_bl),
        float_to_int16(drive_br),
        float_to_int16(intake_power),
        norm01_to_u16(arm_base_pos),
        norm01_to_u16(wrist_pos),
        norm01_to_u16(claw_pos),
        norm01_to_u16(climb_pos),
        norm01_to_u16((arm_extend_power + 1.0) / 2.0),  # -1..1 -> 0..1
        flags,
        0,  # reserved
        int(max(0, min(65535, wheel_rpm)))
    )
    return data

# ---------- Robot control client ----------
class RobotClient:
    def __init__(self, server_url):
        self.ws = websocket.WebSocketApp(
            server_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )
        self.lock = threading.Lock()
        self.controller_state = self.default_controller_state()
        self.robot_cmd = default_robot_command()
        self.stop_event = threading.Event()
        self.connected_ws = False

        try:
            self.serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
            print(f"[Robot] Serial connected on {SERIAL_PORT}")
        except Exception as e:
            self.serial = None
            print(f"[Robot] Serial open failed: {e}")

    def default_controller_state(self):
        return {
            "id": 10,
            "left_stick_x": 0.0, "left_stick_y": 0.0,
            "right_stick_x": 0.0, "right_stick_y": 0.0,
            "left_stick_button": False, "right_stick_button": False,
            "button_a": False, "button_b": False,
            "button_x": False, "button_y": False,
            "button_left_bumper": False, "button_right_bumper": False,
            "button_center": False, "button_left": False, "button_right": False,
            "dpad_top": False, "dpad_left": False,
            "dpad_right": False, "dpad_bottom": False,
            "trigger_left": 0.0, "trigger_right": 0.0
        }

    # --- WebSocket callbacks ---
    def on_open(self, ws):
        print("[Robot] WS connected")
        self.connected_ws = True

    def on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
            if msg.get("destination") != ROBOT_SENDER:
                return
            payload = json.loads(msg["data"])
            if payload.get("id") == 10 and msg.get("sender") == CONTROLLER_SENDER:
                with self.lock:
                    self.controller_state.update(payload)
        except Exception as e:
            print(f"[Robot] WS message error: {e}")

    def on_close(self, ws, code, reason):
        print("[Robot] WS closed:", code, reason)
        self.connected_ws = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Robot] WS error:", error)

    # --- Mapping from controller -> robot_cmd ---
    def update_robot_command_from_controller(self):
        s = self.controller_state
        cmd = self.robot_cmd

        # 1) Drive (mecanum)
        cmd["drive"] = mecanum_blend(
            s["left_stick_x"],
            s["left_stick_y"],
            s["trigger_left"],
            s["trigger_right"]
        )

        # 2) Intake: right bumper in, left bumper out
        if s["button_right_bumper"]:
            cmd["intake_power"] = 1.0
        elif s["button_left_bumper"]:
            cmd["intake_power"] = -1.0
        else:
            cmd["intake_power"] = 0.0

        # 3) Arm base presets (A/B/X/Y)
        if s["button_a"]:
            cmd["arm_base_pos"] = ARM_BASE_PICK
            cmd["wrist_pos"]    = WRIST_PICK
        elif s["button_b"]:
            cmd["arm_base_pos"] = ARM_BASE_DROP_1
            cmd["wrist_pos"]    = WRIST_DROP
        elif s["button_x"]:
            cmd["arm_base_pos"] = ARM_BASE_DROP_2
            cmd["wrist_pos"]    = WRIST_DROP
        elif s["button_y"]:
            cmd["arm_base_pos"] = ARM_BASE_DROP_3
            cmd["wrist_pos"]    = WRIST_DROP

        # 4) Claw open/close: D-pad up/down
        if s["dpad_top"]:
            cmd["claw_pos"] = CLAW_OPEN
        elif s["dpad_bottom"]:
            cmd["claw_pos"] = CLAW_CLOSED

        # 5) Linear arm extension: right stick Y (manual)
        ext = apply_deadzone(s["right_stick_y"])
        cmd["arm_extend_power"] = clamp(ext)

        # 6) Climb presets: left/center/right buttons
        if s["button_left"]:
            cmd["climb_pos"] = CLIMB_STOW
        if s["button_center"]:
            cmd["climb_pos"] = CLIMB_HOOK
        if s["button_right"]:
            cmd["climb_pos"] = CLIMB_UP

        # 7) Voltage device: left stick button as placeholder
        cmd["voltage_device_on"] = s["left_stick_button"]

        # 8) RPM wheel: right stick X → target
        cmd["wheel_rpm_target"] = int((apply_deadzone(s["right_stick_x"]) + 1.0) * 0.5 * 65535)

        self.robot_cmd = cmd

    def serial_loop(self):
        period = 1.0 / UPDATE_HZ
        while not self.stop_event.is_set():
            with self.lock:
                self.update_robot_command_from_controller()
                cmd = self.robot_cmd.copy()

            if self.serial and self.serial.is_open:
                try:
                    data = pack_robot_command(cmd)
                    self.serial.write(data)
                except Exception as e:
                    print(f"[Robot] Serial write error: {e}")

            time.sleep(period)

    def shutdown(self, *_):
        print("\n[Robot] Shutting down...")
        self.stop_event.set()
        try:
            self.ws.close()
        except:
            pass
        if self.serial and self.serial.is_open:
            self.serial.close()

    def run(self):
        t = threading.Thread(target=self.serial_loop, daemon=True)
        t.start()
        signal.signal(signal.SIGINT, self.shutdown)
        self.ws.run_forever(ping_interval=10, ping_timeout=5)

# ---------- Camera sender client ----------
class CameraClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.ws = None
        self.stop_event = threading.Event()
        self.connected = False

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error
        )
        t = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 10, "ping_timeout": 5}, daemon=True)
        t.start()

    def on_open(self, ws):
        print("[Camera] WS connected")
        self.connected = True

    def on_close(self, ws, code, reason):
        print("[Camera] WS closed:", code, reason)
        self.connected = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Camera] WS error:", error)

    def send_frame(self, jpg_bytes):
        if not self.connected:
            return
        # base64-encode JPEG for easier handling on the UI side
        b64 = base64.b64encode(jpg_bytes).decode("ascii")
        payload = {
            "id": 20,
            "ts": time.time(),
            "frame_b64": b64
        }
        envelope = {
            "sender": CAM_SENDER,
            "destination": CAM_DESTINATION,
            "data": json.dumps(payload)
        }
        try:
            self.ws.send(json.dumps(envelope))
        except Exception as e:
            print(f"[Camera] send error: {e}")

    def shutdown(self):
        self.stop_event.set()
        try:
            self.ws.close()
        except:
            pass

def camera_loop(cam_client: CameraClient):
    cap = cv2.VideoCapture(CAM_DEVICE_INDEX)
    if not cap.isOpened():
        print("[Camera] Failed to open camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAM_FPS)

    period = 1.0 / CAM_FPS
    while not cam_client.stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Optional: downscale / compress more
        # frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        if ok:
            cam_client.send_frame(jpg.tobytes())

        time.sleep(period)

    cap.release()
    print("[Camera] Loop ended")

# ---------- Main ----------
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Tip: for serial, add your user to 'dialout' or run with sudo.")

    robot = RobotClient(SERVER_URL)
    cam_client = CameraClient(SERVER_URL)

    # Start camera WS connection & loop
    cam_client.connect()
    cam_thread = threading.Thread(target=camera_loop, args=(cam_client,), daemon=True)
    cam_thread.start()

    try:
        robot.run()
    except KeyboardInterrupt:
        pass

    robot.shutdown()
    cam_client.shutdown()