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
import tomllib

constants = {}

# ---------- Helpers ----------
def clamp(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))

def apply_deadzone(v, dz):
    return 0.0 if abs(v) < dz else v

def normalize_wheels(wheels: List[float]) -> List[float]:
    m = max(abs(w) for w in wheels)
    return [w / m for w in wheels] if m > 1.0 else wheels

def mecanum_blend(x: float, y: float, w: float) -> List[float]:
    vx = clamp(apply_deadzone(x, constants["DEADZONE"]))      # forward/back
    vy = clamp(apply_deadzone(y, constants["DEADZONE"]))      # strafe right-left
    omega = clamp(apply_deadzone(w, constants["DEADZONE"]))   # turn

    fl = vx + vy + omega
    fr = vx - vy - omega
    bl = vx - vy + omega
    br = vx + vy - omega
    return normalize_wheels([fl, fr, bl, br])

# ---------- Robot command struct (Pi -> Pico) ----------
# needs to be between 0 and 255. assumes speed is a signed percentage float.
def scale_motor_speed(speed: float) -> int:
    return int(127 * speed) + 127

# needs to be between 0 and 255. assumes pos is degrees.
def scale_servo_pos(pos: float) -> int:
     return int(pos * 255) #FIXME do I need a 360 or 2pi somewhere in here???


#FIXME are these good default values?
@dataclass
class RobotCommand:
    left_front_drive_motor: float = 0.0
    left_back_drive_motor: float = 0.0
    right_front_drive_motor: float = 0.0
    right_back_drive_motor: float = 0.0

    intake_motor: float = 0.0

    arm_servo_pos: float = 0.0
    arm_extend_motor: float = 0.0
    wrist_servo_pos: float = 0.0
    claw_servo_pos: float = 0.0
    
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
    msg = struct.pack(">c11Bc",
                      bytes(constants["START_BYTE"], 'ascii'),
                      scale_motor_speed(cmd.left_front_drive_motor),
                      scale_motor_speed(cmd.left_back_drive_motor),
                      scale_motor_speed(cmd.right_front_drive_motor),
                      scale_motor_speed(cmd.right_back_drive_motor),
                      scale_motor_speed(cmd.arm_extend_motor),
                      scale_motor_speed(cmd.intake_motor),
                      scale_servo_pos(cmd.arm_servo_pos),
                      scale_servo_pos(cmd.wrist_servo_pos),
                      scale_servo_pos(cmd.claw_servo_pos),
                      scale_motor_speed(cmd.climb_motor_speed),
                      cmd.jumpstart_voltage,
                      bytes(constants["END_BYTE"], 'ascii'))
    return msg

# ---------- Robot control client ----------
class RobotClient:
    def __init__(self, server_url, default_command: RobotCommand):
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
        self.default_command = default_command
        self.robot_cmd = default_command
        self.robot_state = RobotState.TELEOP #FIXME only run tele-op for now while testing stuff

        #TODO FIXME have a callback to check FMS periodically? or like... idk man...

        # try to open serial connection to Pico
        self.try_open_serial()

    def try_open_serial(self):
        try:
            self.serial = serial.Serial(constants["SERIAL_PORT"], constants["BAUD_RATE"], timeout=0.5)
            print(f"[Robot] Serial connected on {constants["SERIAL_PORT"]}")
        except Exception as e:
            self.serial = None
            print(f"[Robot] Serial open failed: {e}")

    # --- WebSocket callbacks ---
    def on_open(self, ws):
        print("[Robot] WS connected")

        # send websocket message so the relay server knows where to find us
        ws.send(json.dumps({
            "sender": constants["ROBOT_NAME"],
            "destination": constants["CONTROLLER_INPUT_NAME"], #FIXME???
            "data": "{}"
        }))

        self.connected_ws = True

    def on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
            if msg.get("destination") != constants["ROBOT_NAME"]:
                return
            
            payload = json.loads(msg["data"])
            msg_id = payload.get("id")

            #TODO FIXME separate one for autonomous???

            # update robot state
            if msg_id == 30 and msg.get("sender") == constants["GUI_NAME"]:
                with self.lock:
                    self.robot_state = payload.get("state")
                    #FIXME autonomous program selector

            # update controller state for robot control
            elif msg_id == 10 and msg.get("sender") == constants["CONTROLLER_INPUT_NAME"]:
                with self.lock:
                    self.controller_state.left_stick_x = payload.get("left_stick_x")
                    self.controller_state.left_stick_y = payload.get("left_stick_y")
                    self.controller_state.right_stick_x = payload.get("right_stick_x")
                    self.controller_state.right_stick_y = payload.get("right_stick_y")
                    self.controller_state.left_stick_button= payload.get("left_stick_button")
                    self.controller_state.right_stick_button= payload.get("right_stick_button")
                    self.controller_state.button_a = payload.get("button_a")
                    self.controller_state.button_b = payload.get("button_b")
                    self.controller_state.button_x = payload.get("button_x")
                    self.controller_state.button_y = payload.get("button_y")
                    self.controller_state.left_bumper = payload.get("left_bumper")
                    self.controller_state.right_bumper = payload.get("right_bumper")
                    self.controller_state.dpad_top = payload.get("dpad_top")
                    self.controller_state.dpad_bottom = payload.get("dpad_bottom")
                    self.controller_state.dpad_left = payload.get("dpad_left")
                    self.controller_state.dpad_right= payload.get("dpad_right")
                    self.controller_state.trigger_left = payload.get("trigger_left")
                    self.controller_state.trigger_right = payload.get("trigger_right")
            
            # update robot position/alignment from AprilTag process
            elif msg_id == 141 and msg.get("sender") == constants["APRILTAG_NAME"]:
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
            cmd.intake_motor = constants["INTAKE_IN_SPEED"]
        elif s.left_bumper:
            cmd.intake_motor = constants["INTAKE_OUT_SPEED"]
        else:
            cmd.intake_motor = 0.0

        # Arm: score high/low, grab battery, stow        
        if s.dpad_top:
            cmd.arm_servo_pos = constants["ARM_BASE_HIGH"]
        elif s.dpad_bottom:
            cmd.arm_servo_pos = constants["ARM_BASE_LOW"]
        else:
            pass #TODO FIXME?

        # Wrist: score left/right, grab battery
        if s.dpad_left:
            cmd.wrist_servo_pos = constants["WRIST_LEFT"]
        elif s.dpad_right:
            cmd.wrist_servo_pos = constants["WRIST_RIGHT"]
        else: #FIXME this is bad idea
            cmd.wrist_servo_pos = constants["WRIST_PICK"]

        # Claw: open/close
        if s.button_y:
            cmd.claw_servo_pos = constants["CLAW_OPEN"] # release battery
        elif s.button_a:
            cmd.claw_servo_pos = constants["CLAW_CLOSED"] #TODO FIXME do we have to continuously keep this or will it stay if we only set it once (pico firmware?)

        # Linear arm extension
        if s.button_x:
            cmd.arm_extend_motor = constants["SLIDE_RETRACT_SPEED"]
        elif s.button_b:
            cmd.arm_extend_motor = constants["SLIDE_EXTEND_SPEED"]
        else:
            cmd.arm_extend_motor = constants["SLIDE_STOW_SPEED"]

        # Climber retract/extend
        #TODO
        cmd.climb_motor_speed = 0.0

        # Jumpstart voltage FIXME this just runs 100% of the time lol
        #TODO FIXME

        self.robot_cmd = cmd

    def serial_loop(self):
        while not self.stop_event.is_set():
            cmd = RobotCommand()
            
            with self.lock:
                if self.robot_state == RobotState.OFF:
                    pass #FIXME send like, default command? or no command?
                elif self.robot_state == RobotState.AUTONOMOUS:
                    pass #FIXME need to figure out autonomous
                elif self.robot_state == RobotState.TELEOP:
                    self.update_robot_command_from_controller()
                    cmd = self.robot_cmd

            if self.serial and self.serial.is_open:
                try:
                    data = pack_robot_command(cmd)
                    self.serial.write(data)
                except Exception as e:
                    print(f"[Robot] Serial write error: {e}")

            time.sleep(1.0 / constants["UPDATE_HZ"])

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
        print(print(f"Starting robot code with ID: {t.native_id}"))
        signal.signal(signal.SIGINT, self.shutdown)
        
        self.ws.run_forever(ping_interval=1, ping_timeout=0.5)


# ---------- Main ----------
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Tip: for serial, add your user to 'dialout' or run with sudo.")

    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Robot] Failed to read constants file")
            raise SystemExit

    # have to update this after reading the constants file
    default_robot_command = RobotCommand()
    default_robot_command.arm_servo_pos = constants["ARM_BASE_STOW"]
    default_robot_command.wrist_servo_pos = constants["WRIST_STOW"]
    default_robot_command.claw_servo_pos = constants["CLAW_CLOSED"]

    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    robot = RobotClient(f"{url}:{port}", default_robot_command)

    try:
        robot.run()
    except KeyboardInterrupt:
        pass

    robot.shutdown()
