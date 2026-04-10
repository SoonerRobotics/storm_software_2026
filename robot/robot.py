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
import copy

constants = {}

# ---------- Helpers ----------
def clamp(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))

def apply_deadzone(v, dz):
    return 0.0 if abs(v) < dz else v

def normalize_wheels(wheels: List[float]) -> List[float]:
    m = max(abs(w) for w in wheels)
    return [w / m for w in wheels] if m > 1.0 else wheels

def square_inputs(val: float) -> float:
    sign = -1 if val < 0 else 1
    return sign * (val ** 2)

def mecanum_blend(x: float, y: float, w: float) -> List[float]:
    vx = clamp(apply_deadzone(square_inputs(x), constants["DEADZONE"]), -constants["MAX_DRIVE_SPEED"], constants["MAX_DRIVE_SPEED"])      # forward/back
    vy = clamp(apply_deadzone(square_inputs(y), constants["DEADZONE"]), -constants["MAX_DRIVE_SPEED"], constants["MAX_DRIVE_SPEED"])      # strafe right-left
    omega = clamp(apply_deadzone(square_inputs(w), constants["DEADZONE"]), -constants["MAX_TURN_SPEED"], constants["MAX_TURN_SPEED"])     # turn

    fl = vx + vy + omega
    fr = vx - vy - omega
    bl = vx - vy + omega
    br = vx + vy - omega
    return normalize_wheels([-fl, fr, -bl, br]) # left are negative because motors are reversed

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

    charge_motor_speed: float = 0.0

    jumpstart_voltage: int = 0

    connected: bool = False # for loss-of-signal

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


class TimedRobotCommand:
    def __init__(self, command: RobotCommand, timeout: float):
        self.command = command
        self.timeout = timeout
        
        self.time = -1
    
    def start(self):
        self.time = time.time()

    def is_done(self) -> bool:
        if (time.time() - self.time) > self.timeout:
            return True
        return False

class AutonomousSequence:
    def __init__(self, commands: List[TimedRobotCommand]):
        self.commands = commands
        self.index = 0

        self.started = False

    def start(self):
        self.index = 0
        self.commands[self.index].start()

        self.started = True
    
    def run(self):
        if self.commands[self.index].is_done():
            self.index += 1
        
        if self.index >= len(self.commands)+1:
            return
        
        return self.commands[self.index] #FIXME???

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

# ======== Autonomous Programs ========
driveForwards = RobotCommand()
# driveForwards.left_front_drive_motor,  \
# driveForwards.right_front_drive_motor, \
# driveForwards.left_back_drive_motor,   \
# driveForwards.right_back_drive_motor = mecanum_blend(0.4, 0.0, 0.0)

extendSlide = RobotCommand()
# extendSlide.arm_extend_motor = constants["SLIDE_EXTEND_SPEED"]

flipWrist = RobotCommand()
# flipWrist.wrist_servo_pos = constants["WRIST_LEFT"]



# need to keep wrist at same position (idk if this is even worth it?)
openClaw = copy.copy(flipWrist)
# openClaw.claw_servo_pos = constants["CLAW_OPEN"]

DriveForwardAutonomous = AutonomousSequence([
    TimedRobotCommand(driveForwards, 5.0), # 5 seconds
    TimedRobotCommand(RobotCommand(), 2) # and stop?
])

ScoreOneAutonomous = AutonomousSequence([
    TimedRobotCommand(driveForwards, 5.0), # position ourselves
    TimedRobotCommand(RobotCommand(), 2),  # stop
    TimedRobotCommand(extendSlide, 1),     #FIXME I don't think this is long enough?
    TimedRobotCommand(flipWrist, 1),       # 1 second should be good? should also automatically not trigger claw?
    TimedRobotCommand(openClaw, 1),        # do we want to drive further after this?
])
# =====================================

# generate serial message to be sent to Pico
def pack_robot_command(cmd: RobotCommand) -> bytes:
    # okay so this is assuming we're doing a mega-message and not variable-size messages
    # so no COMMAND bytes, but keeping the start and end bytes

    #FIXME is it supposed to be little or big endian?
    msg = struct.pack(
        ">c13Bc",
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
        scale_motor_speed(cmd.charge_motor_speed),
        cmd.jumpstart_voltage,
        cmd.connected,
        bytes(constants["END_BYTE"], 'ascii')
    )

    return msg

# ---------- Robot control client ----------
class RobotClient:
    def __init__(self, server_url, default_command: RobotCommand, autos: List[AutonomousSequence]):
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
        self.last_controller_state  = ControllerState()

        self.arm_poses = [constants["ARM_BASE_PICK"], constants["ARM_BASE_STOW"], constants["ARM_BASE_LOW"], constants["ARM_BASE_HIGH"], constants["ARM_BASE_CLIMB"]]
        self.wrist_poses = [constants["WRIST_LEFT"], constants["WRIST_STOW"], constants["WRIST_RIGHT"]]
        self.arm_index = 1 # start in the middle
        self.wrist_index = 1 # start in the middle
        self.claw_toggle = False

        self.default_command = default_command
        self.robot_cmd = default_command
        self.robot_state = RobotState.TELEOP

        self.autonomous_programs = autos
        self.auto_idx = 0 #FIXME?

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
                    self.last_controller_state = copy.copy(self.controller_state)

                    self.controller_state.left_stick_x = payload.get("left_stick_x")
                    self.controller_state.left_stick_y = payload.get("left_stick_y")
                    self.controller_state.right_stick_x = payload.get("right_stick_x")
                    self.controller_state.right_stick_y = payload.get("right_stick_y")
                    self.controller_state.left_stick_button = payload.get("left_stick_button")
                    self.controller_state.right_stick_button = payload.get("right_stick_button")
                    self.controller_state.button_a = payload.get("button_a")
                    self.controller_state.button_b = payload.get("button_b")
                    self.controller_state.button_x = payload.get("button_x")
                    self.controller_state.button_y = payload.get("button_y")
                    self.controller_state.left_bumper = payload.get("button_left_bumper")
                    self.controller_state.right_bumper = payload.get("button_right_bumper")
                    self.controller_state.dpad_top = payload.get("dpad_top")
                    self.controller_state.dpad_bottom = payload.get("dpad_bottom")
                    self.controller_state.dpad_left = payload.get("dpad_left")
                    self.controller_state.dpad_right= payload.get("dpad_right")
                    self.controller_state.trigger_left = payload.get("trigger_left")
                    self.controller_state.trigger_right = payload.get("trigger_right")
            
            # update robot position/alignment from AprilTag process
            elif msg_id == 141 and msg.get("sender") == constants["APRILTAG_NAME"]:
                with self.lock:
                    self.tag_id = payload.get("ids")
                    self.field_x = payload.get("x")
                    self.field_y = payload.get("y")
                    self.field_heading = payload.get("heading")
                    self.camera_x_diff = payload.get("x_diff")
                    self.camera_y_diff = payload.get("y_diff")
                    self.camera_rot = payload.get("rot")
                pass 

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
        cmd.right_front_drive_motor, \
        cmd.left_back_drive_motor,   \
        cmd.right_back_drive_motor = mecanum_blend(s.left_stick_y, s.left_stick_x, s.right_stick_x)###

        #Auto alignment: right stick button hold
        if s.right_stick_button:
            rot_dir = 0
            hor_amt = 0 
            dep_amt = 0
            
            #Rotate to face tag
            if not abs(self.camera_rot) > 3:
                
                cmd.left_front_drive_motor,  \
                cmd.right_front_drive_motor, \
                cmd.left_back_drive_motor,   \
                cmd.right_back_drive_motor = mecanum_blend(s.left_stick_y, s.left_stick_x, rot_dir)###
                if self.camera_rot < -3:
                    rot_dir = 0.2 #Change this to be more real rotation (idk what good numbers are)
                elif self.camera_rot > 3:
                    rot_dir = -0.2 #Change this to be more real rotation (idk what good numbers are)
                else:
                    rot_dir = 0
            
            #Center to tag
            if not abs(self.camera_x_diff) > 0.5:
                cmd.left_front_drive_motor,  \
                cmd.right_front_drive_motor, \
                cmd.left_back_drive_motor,   \
                cmd.right_back_drive_motor = mecanum_blend(s.left_stick_y, hor_amt, s.right_stick_x)###
                if self.camera_x_diff > 0.5:
                    hor_amt = 0.2 #Change this to be more real translation (idk what good numbers are)
                elif self.camera_x_diff < -0.5:
                    hor_amt = -0.2 #Change this to be more real translation (idk what good numbers are)
                else:
                    hor_amt = 0
            
            #Depth Alignment
            if not abs(self.camera_y_diff) > 17.5:
                cmd.left_front_drive_motor,  \
                cmd.right_front_drive_motor, \
                cmd.left_back_drive_motor,   \
                cmd.right_back_drive_motor = mecanum_blend(dep_amt, s.left_stick_x, s.right_stick_x)
                if self.camera_y_diff < 17.5:
                    dep_amt = -0.2 #Change this to be more real translation (idk what good numbers are)
                elif self.camera_y_diff > 17.5:
                    dep_amt = 0.2 #Change this to be more real translation (idk what good numbers are)
                else:
                    dep_amt = 0

        # Intake: right bumper in, left bumper out
        if s.right_bumper:
            cmd.intake_motor = constants["INTAKE_IN_SPEED"]
        elif s.left_bumper:
            cmd.intake_motor = constants["INTAKE_OUT_SPEED"]
        else:
            cmd.intake_motor = 0.0

        # Arm: score high/low, grab battery, stow
        if s.dpad_top and not self.last_controller_state.dpad_top and self.arm_index < (len(self.arm_poses) - 1):
            self.arm_index += 1
        elif s.dpad_bottom and not self.last_controller_state.dpad_bottom and self.arm_index > 0:
            self.arm_index -= 1
        
        cmd.arm_servo_pos = self.arm_poses[self.arm_index]


        # Wrist: score left/right, grab battery
        if s.dpad_right and not self.last_controller_state.dpad_right and self.wrist_index < (len(self.wrist_poses) - 1):
            self.wrist_index += 1
        elif s.dpad_left and not self.last_controller_state.dpad_left and self.wrist_index > 0:
            self.wrist_index -= 1
        
        cmd.wrist_servo_pos = self.wrist_poses[self.wrist_index]

        # Claw: open/close toggle
        # print(s.button_a)
        if s.button_a and not self.last_controller_state.button_a:
            self.claw_toggle = not self.claw_toggle

        if self.claw_toggle:
            cmd.claw_servo_pos = constants["CLAW_OPEN"]
        else:
            cmd.claw_servo_pos = constants["CLAW_CLOSED"]

        # Linear arm extension
        if s.button_x:
            cmd.arm_extend_motor = constants["SLIDE_RETRACT_SPEED"]
        elif s.button_b:
            cmd.arm_extend_motor = constants["SLIDE_EXTEND_SPEED"]
        else:
            cmd.arm_extend_motor = constants["SLIDE_STOW_SPEED"]

        # Climber retract/extend
        if s.button_y: # only while held for safety
            cmd.climb_motor_speed = constants["CLIMB_SPEED"]
        else:
            cmd.climb_motor_speed = 0.0 #FIXME we might need to run it backwards too? maybe?

        # Jumpstart voltage FIXME this just runs 100% of the time lol
        cmd.jumpstart_voltage = 6

        # Charging wheel speed FIXME this just runs 100% of the time lol and also can't be controlled
        cmd.charge_motor_speed = 0.5

        # loss of signal checkb
        cmd.connected = self.connected_ws

        self.robot_cmd = cmd
    
    def update_robot_command_from_autonomous(self):
        if not self.autonomous_programs[self.auto_idx].started:
            self.autonomous_programs[self.auto_idx].start()
        
        auto_cmd = self.autonomous_programs[self.auto_idx].run()
        if auto_cmd is not None:
            self.robot_cmd = auto_cmd

    def serial_loop(self):
        while not self.stop_event.is_set():
            cmd = RobotCommand()
            
            with self.lock:
                if self.robot_state == RobotState.OFF:
                    pass #FIXME send like, default command? or no command?
                elif self.robot_state == RobotState.AUTONOMOUS:
                    self.update_robot_command_from_autonomous()
                elif self.robot_state == RobotState.TELEOP:
                    self.update_robot_command_from_controller()
                    cmd = self.robot_cmd

            #FIXME does this even need to be here?
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
    default_robot_command.arm_servo_pos = constants["ARM_BASE_LOW"]
    default_robot_command.wrist_servo_pos = constants["WRIST_STOW"]
    default_robot_command.claw_servo_pos = constants["CLAW_CLOSED"]

    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    robot = RobotClient(f"{url}:{port}", default_robot_command, [DriveForwardAutonomous, ScoreOneAutonomous])

    try:
        robot.run()
    except KeyboardInterrupt:
        pass

    robot.shutdown()
