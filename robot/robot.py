from dataclasses import dataclass
from enum import Enum
import json
import time
from typing import List
import websocket
import threading
import signal
import serial
import struct
import os

from constants.constants import APRILTAG_SENDER, CONTROLLER_SENDER, GUI_SENDER, ROBOT_SENDER, SERVER_URL

# Controller configuration
DEADZONE   = 0.05
UPDATE_HZ   = 50.0

# Pico 2 (PCB/electrical) config
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 115200
START_BYTE = b"$"
END_BYTE = b"!"

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

class RobotState(Enum):
    OFF = 0
    AUTONOMOUS = 1
    TELEOP = 2
    TEST = 3

class ArmState(Enum):
    STOWED = 0 # starting configuration
    PICKING_UP = 1
    SCORING_LOW = 2
    SCORING_HIGH = 3

# generate serial message to be sent to Pico
def pack_robot_command(cmd: RobotCommand) -> bytes:
    # okay so this is assuming we're doing a mega-message and not variable-size messages
    # so no COMMAND bytes, but keeping the start and end bytes

    #FIXME is it supposed to be little or big endian?
    msg = struct.pack(">c14Bc",
                      START_BYTE,
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
                      END_BYTE)
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
        self.robot_state = RobotState.OFF #FIXME ???

        #TODO FIXME have a callback to check FMS periodically? or like... idk man...

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
            msg_id = payload.get("id")

            #TODO FIXME separate one for autonomous???

            # update robot state
            if msg_id == 30 and msg.get("sender") == GUI_SENDER:
                pass #TODO FIXME update robot state

            # update controller state for robot control
            elif msg_id == 10 and msg.get("sender") == CONTROLLER_SENDER:
                with self.lock:
                    self.controller_state.left_stick_x = payload.get("left_stick_x")
                    self.controller_state.left_stick_y = payload.get("left_stick_y")
                    self.controller_state.right_stick_x = payload.get("right_stick_x")
                    self.controller_state.right_stick_y = payload.get("right_stick_y")
                    self.controller_state.left_stick_button= payload.get("left_stick_button")
                    self.controller_state.right_stick_button= payload.get("right_stick_button")
                    self.controller_state.button_a= payload.get("button_a")
                    self.controller_state.button_b= payload.get("button_b")
                    self.controller_state.button_x= payload.get("button_x")
                    self.controller_state.button_y= payload.get("button_y")
                    self.controller_state.left_bumper= payload.get("left_bumper")
                    self.controller_state.right_bumper= payload.get("right_bumper")
                    self.controller_state.dpad_top= payload.get("dpad_top")
                    self.controller_state.dpad_bottom= payload.get("dpad_bottom")
                    self.controller_state.dpad_left= payload.get("dpad_left")
                    self.controller_state.dpad_right= payload.get("dpad_right")
                    self.controller_state.trigger_left = payload.get("trigger_left")
                    self.controller_state.trigger_right = payload.get("trigger_right")
            
            # update robot position/alignment from AprilTag process
            elif msg_id == 141 and msg.get("sender") == APRILTAG_SENDER:
                pass #TODO

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

        # Drive (mecanum)
        cmd.left_front_drive_motor,  \
        cmd.left_back_drive_motor,   \
        cmd.right_front_drive_motor, \
        cmd.right_back_drive_motor = mecanum_blend(s.left_stick_x, s.left_stick_y, s.right_stick_x)

        # Intake: right bumper in, left bumper out
        if s.right_bumper:
            cmd.intake_motor = INTAKE_IN_SPEED
        elif s.left_bumper:
            cmd.intake_motor = INTAKE_OUT_SPEED
        else:
            cmd.intake_motor = 0.0

        # Arm: score high/low, grab battery, stow        
        if s.dpad_top:
            cmd.arm_servo_pos = ARM_BASE_HIGH
        elif s.dpad_bottom:
            cmd.arm_servo_pos = ARM_BASE_LOW
        else:
            pass #TODO FIXME?

        # Wrist: score left/right, grab battery
        if s.dpad_left:
            cmd.wrist_servo_pos = WRIST_LEFT
        elif s.dpad_right:
            cmd.wrist_servo_pos = WRIST_RIGHT
        else: #FIXME this is bad idea
            cmd.wrist_servo_pos = WRIST_PICK

        # Claw: open/close
        if s.button_y:
            cmd.claw_servo_pos = CLAW_OPEN # release battery
        elif s.button_a:
            cmd.claw_servo_pos = CLAW_CLOSED #TODO FIXME do we have to continuously keep this or will it stay if we only set it once (pico firmware?)

        # Linear arm extension
        if s.button_x:
            cmd.arm_extend_motor = SLIDE_RETRACT_SPEED
        elif s.button_b:
            cmd.arm_extend_motor = SLIDE_EXTEND_SPEED
        else:
            cmd.arm_extend_motor = SLIDE_STOW_SPEED

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


# ---------- Main ----------
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Tip: for serial, add your user to 'dialout' or run with sudo.")

    robot = RobotClient(SERVER_URL)

    try:
        robot.run()
    except KeyboardInterrupt:
        pass

    robot.shutdown()