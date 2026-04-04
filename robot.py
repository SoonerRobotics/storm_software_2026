from dataclasses import dataclass
import json
import time
from typing import List
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

# Controller configuration
DEADZONE   = 0.05
UPDATE_HZ   = 50.0

# Pico 2 (PCB/electrical) config
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200
START_BYTE = b"$"
END_BYTE = b"!"

# Camera config
CAM_DEVICE_INDEX = 0          # /dev/video0
CAM_WIDTH        = 640
CAM_HEIGHT       = 360
CAM_FPS          = 10.0       # desired send rate

# ---------- Preset positions (0.0-1.0 normalized) ----------
ARM_BASE_STOW  = 0.8
ARM_BASE_PICK   = 0.5
ARM_BASE_LOW = 0.6
ARM_BASE_HIGH = 0.7

WRIST_STOW   = 0.2
WRIST_PICK   = 0.7
WRIST_LEFT   = 0.5
WRIST_RIGHT   = 0.5

CLAW_OPEN    = 0.2
CLAW_CLOSED  = 0.8

SLIDE_EXTEND_SPEED = 0.1
SLIDE_RETRACT_SPEED = -0.1
SLIDE_STOW_SPEED = -0.05

INTAKE_IN_SPEED = 0.5
INTAKE_OUT_SPEED = -0.3

CLIMB_STOW   = 0.0
CLIMB_HOOK   = 0.5
CLIMB_UP     = 1.0

MAX_DRIVE_SPEED = 1.0
MAX_TURN_SPEED = 1.0

# ---------- Helpers ----------
def clamp(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))

def apply_deadzone(v, dz=DEADZONE):
    return 0.0 if abs(v) < dz else v

def normalize_wheels(wheels: List[float]) -> List[float]:
    m = max(abs(w) for w in wheels)
    return [w / m for w in wheels] if m > 1.0 else wheels

def mecanum_blend(x: float, y: float, w: float) -> List[float]:
    vx = clamp(apply_deadzone(x))      # forward/back
    vy = clamp(apply_deadzone(y))      # strafe right-left
    omega = clamp(apply_deadzone(w))   # turn

    fl = vx + vy + omega
    fr = vx - vy - omega
    bl = vx - vy + omega
    br = vx + vy - omega
    return normalize_wheels([fl, fr, bl, br])

# ---------- Robot command struct (Pi -> Pico) ----------
# needs to be between 0 and 255. assumes speed is a signed percentage float.
def scale_motor_speed(speed: float) -> int:
    return int(127 * speed) + 127

# needs to be between 0 and 255. assumes pos is degrees. FIXME do we even need this?
# def normalize_servo_pos(pos: int) -> float:
#     return float(pos / 360.0)


#FIXME are these good default values?
@dataclass
class RobotCommand:
    left_front_drive_motor: float = 0.0
    left_back_drive_motor: float = 0.0
    right_front_drive_motor: float = 0.0
    right_back_drive_motor: float = 0.0

    intake_motor: float = 0.0

    arm_servo_pos: float = ARM_BASE_STOW
    arm_extend_motor: float = 0.0
    wrist_servo_pos: float = WRIST_STOW
    claw_servo_pos: float = CLAW_CLOSED
    
    climb_motor_speed: float = 0.0

    jumpstart_voltage: int = 0

@dataclass
class ControllerState:
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0

    left_stick_button: bool = False
    right_stick_button: bool = False

    button_a: bool = False
    button_b: bool = False
    button_x: bool = False
    button_y: bool = False

    left_bumper: bool = False
    right_bumper: bool = False

    dpad_top: bool = False
    dpad_bottom: bool = False
    dpad_left: bool = False
    dpad_right: bool = False

    trigger_left: float = 0.0
    trigger_right: float = 0.0

# generate serial message to be sent to Pico
def pack_robot_command(cmd: RobotCommand) -> bytes:
    # okay so this is assuming we're doing a mega-message and not variable-size messages
    # so no COMMAND bytes, but keeping the start and end bytes

    #FIXME is it supposed to be little or big endian?
    msg = struct.pack(">c14Bc",
                      "$",
                      scale_motor_speed(cmd.left_front_drive_motor),
                      scale_motor_speed(cmd.left_back_drive_motor),
                      scale_motor_speed(cmd.right_front_drive_motor),
                      scale_motor_speed(cmd.right_back_drive_motor),
                      scale_motor_speed(cmd.arm_extend_motor),
                      scale_motor_speed(cmd.intake_motor),
                      cmd.arm_servo_pos,
                      cmd.wrist_servo_pos,
                      cmd.claw_servo_pos,
                      scale_motor_speed(cmd.climb_motor_speed),
                      cmd.jumpstart_voltage,
                      "!")
    return msg

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
        self.connected_ws = False

        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        self.controller_state = ControllerState()
        self.robot_cmd = RobotCommand()

        # try to open serial connection to Pico
        self.try_open_serial()

    def try_open_serial(self):
        try:
            self.serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
            print(f"[Robot] Serial connected on {SERIAL_PORT}")
        except Exception as e:
            self.serial = None
            print(f"[Robot] Serial open failed: {e}")

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
                    #FIXME
                    self.controller_state = ControllerState()
                    self.controller_state.button_a = payload.get("button_a")

        except Exception as e:
            print(f"[Robot] WS message error: {e}")

    def on_close(self, ws, code, reason):
        print("[Robot] WS closed:", code, reason)

        #TODO: send a 'kill everything' message to robot?

        self.connected_ws = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Robot] WS error:", error)

    # --- Mapping from controller -> robot_cmd ---
    def update_robot_command_from_controller(self):
        s = self.controller_state
        cmd = self.robot_cmd

        # 1) Drive (mecanum)
        cmd.left_front_drive_motor,  \
        cmd.left_back_drive_motor,   \
        cmd.right_front_drive_motor, \
        cmd.right_back_drive_motor = mecanum_blend(s.left_stick_x, s.left_stick_y, s.right_stick_x)

        # 2) Intake: right bumper in, left bumper out
        #TODO FIXME

        # 3) Arm base presets (A/B/X/Y)
        #TODO FIXME

        # 4) Claw open/close: D-pad up/down
        #TODO FIXME

        # 5) Linear arm extension: right stick Y (manual)
        #TODO FIXME

        # 6) Climb presets: left/center/right buttons
        #TODO FIXME

        # 7) Voltage device: left stick button as placeholder
        #TODO FIXME

        self.robot_cmd = cmd

    def serial_loop(self):
        while not self.stop_event.is_set():
            with self.lock:
                self.update_robot_command_from_controller()
                cmd = self.robot_cmd

            if self.serial and self.serial.is_open:
                try:
                    data = pack_robot_command(cmd)
                    self.serial.write(data)
                except Exception as e:
                    print(f"[Robot] Serial write error: {e}")

            time.sleep(1.0 / UPDATE_HZ)

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
        
        self.ws.run_forever(ping_interval=1, ping_timeout=5)

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