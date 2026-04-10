import json
import time
import websocket
import threading
import signal
import pygame
import tomllib
import os

constants = {}

# button bindings for Xbox One bluetooth controller
class XboxOneController:
    def __init__(self, idx=0):
        self.joy = pygame.joystick.Joystick(idx)
        self.joy.init()

    def get_left_stick_x(self) -> float:
        return self.joy.get_axis(0)

    def get_left_stick_y(self) -> float:
        return self.joy.get_axis(1)

    def get_right_stick_x(self) -> float:
        return self.joy.get_axis(3)

    def get_right_stick_y(self) -> float:
        return self.joy.get_axis(4)

    def get_trigger_left(self) -> float:
        return self.joy.get_axis(2) #FIXME

    def get_trigger_right(self) -> float:
        return self.joy.get_axis(5) #FIXME

    def get_button_a(self) -> bool:
        return self.joy.get_button(0)

    def get_button_b(self) -> bool:
        return self.joy.get_button(1)

    def get_button_x(self) -> bool:
        return self.joy.get_button(3)

    def get_button_y(self) -> bool:
        return self.joy.get_button(4)

    def get_button_left_bumper(self) -> bool:
        return self.joy.get_button(5)

    def get_button_right_bumper(self) -> bool:
        return self.joy.get_button(6)

    def get_button_center(self) -> bool:
        # return self.joy.get_button(11)
        return False #FIXME idk why but pygame says these are invalid buttons???

    def get_button_left(self) -> bool:
        return self.joy.get_button(7)

    def get_button_right(self) -> bool:
        return self.joy.get_button(8)

    def get_left_stick_button(self) -> bool:
        # return self.joy.get_button(9)
        return False #FIXME idk why but pygame says these are invalid buttons???

    def get_right_stick_button(self) -> bool:
        # return self.joy.get_button(10)
        return False #FIXME idk why but pygame says these are invalid buttons???

    def get_dpad_left(self) -> bool:
        return self.joy.get_hat(0)[0] == -1

    def get_dpad_right(self) -> bool:
        return self.joy.get_hat(0)[0] == 1

    def get_dpad_top(self) -> bool:
        return self.joy.get_hat(0)[1] == -1

    def get_dpad_bottom(self) -> bool:
        return self.joy.get_hat(0)[1] == 1

# button bindings for Xbox One bluetooth controller when connected to Linux
# THIS IS THE ONE WE WILL BE ACTUALLY USING AT COMPETITION
class LinuxXboxOneController:
    def __init__(self, idx=0):
        self.joy = pygame.joystick.Joystick(idx)
        self.joy.init()

        self.debounce_seconds = 0.01
    
    # debounce a button 'cause it's kinda bad
    def debounce(self, curr_val, last_val, last_time):
        # on a change
        if curr_val is not last_val:
            # if it hasn't been long enough
            if (time.time() - last_time) < self.debounce_seconds:
                return last_val, last_time # don't change it
            else:
                # otherwise then it has been long enough
                return curr_val, time.time() # on an edge

        return curr_val, last_time

    def get_left_stick_x(self) -> float:
        return self.joy.get_axis(0)

    def get_left_stick_y(self) -> float:
        return self.joy.get_axis(1)

    def get_right_stick_x(self) -> float:
        return self.joy.get_axis(3)

    def get_right_stick_y(self) -> float:
        return self.joy.get_axis(2)

    def get_trigger_left(self) -> float:
        return (self.joy.get_axis(5) + 1)/2

    def get_trigger_right(self) -> float:
        return (self.joy.get_axis(4) + 1)/2

    def get_button_a(self, last_val, last_time) -> bool:
        x, y = self.debounce(self.joy.get_button(0), last_val, last_time)
        # print(x)
        return x, y

    def get_button_b(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(1), last_val, last_time)

    def get_button_x(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(3), last_val, last_time)

    def get_button_y(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(4), last_val, last_time)

    def get_button_left_bumper(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(6), last_val, last_time)

    def get_button_right_bumper(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(7), last_val, last_time)

    def get_button_center(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(12), last_val, last_time)
        
    def get_button_left(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(10), last_val, last_time)

    def get_button_right(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(11), last_val, last_time)

    def get_left_stick_button(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(13), last_val, last_time)
        
    def get_right_stick_button(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_button(14), last_val, last_time)
        
    def get_dpad_left(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_hat(0)[0] == -1, last_val, last_time)

    def get_dpad_right(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_hat(0)[0] == 1, last_val, last_time)

    def get_dpad_top(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_hat(0)[1] == 1, last_val, last_time)

    def get_dpad_bottom(self, last_val, last_time) -> bool:
        return self.debounce(self.joy.get_hat(0)[1] == -1, last_val, last_time)

# ----------------------------
# Controller Client Class
# ----------------------------
class ControllerClient:
    def __init__(self, server_url):
        self.ws = websocket.WebSocketApp(
            server_url,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error
        )
        self.connected = False
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.controller_state = self.default_state()
        self.last_controller_state = self.default_state()

        self.last_times = {
            "id": 10,
            "left_stick_x": 0.0,
            "left_stick_y": 0.0,
            "right_stick_x": 0.0,
            "right_stick_y": 0.0,
            "left_stick_button": 0.0,
            "right_stick_button": 0.0,
            "button_a": 0.0,
            "button_b": 0.0,
            "button_x": 0.0,
            "button_y": 0.0,
            "button_left_bumper": 0.0,
            "button_right_bumper": 0.0,
            "button_center": 0.0,
            "button_left": 0.0,
            "button_right": 0.0,
            "dpad_top": 0.0,
            "dpad_left": 0.0,
            "dpad_right": 0.0,
            "dpad_bottom": 0.0,
            "trigger_left": 0.0,
            "trigger_right": 0.0
        }

        self.joystick = None 

    # >> WebSocket callbacks (Moved above __init__ to fix AttributeError) <<
    def on_open(self, ws):
        print("[Controller] Connected to server")
        self.connected = True
        time.sleep(0.5) # Keep the delay for server timing
        msg11 = {"id": 11, "connection_status": True}
        
        msg = {
            "sender": constants["CONTROLLER_INPUT_NAME"],
            "destination": constants["ROBOT_NAME"],
            "data": json.dumps(msg11)
        }

        try:
            ws.send(json.dumps(msg))
        except Exception as e:
            #FIXME
            print(e)

    def on_close(self, ws, close_status_code, close_msg):
        print("[Controller] Disconnected from server")
        self.connected = False
        self.stop_event.set()
        pygame.quit()

    def on_error(self, ws, error):
        print("[Controller] WebSocket error:", error)
        self.stop_event.set()

    def default_state(self):
        return {
            "id": 10,
            "left_stick_x": 0.0,
            "left_stick_y": 0.0,
            "right_stick_x": 0.0,
            "right_stick_y": 0.0,
            "left_stick_button": False,
            "right_stick_button": False,
            "button_a": False,
            "button_b": False,
            "button_x": False,
            "button_y": False,
            "button_left_bumper": False,
            "button_right_bumper": False,
            "button_center": False,
            "button_left": False,
            "button_right": False,
            "dpad_top": False,
            "dpad_left": False,
            "dpad_right": False,
            "dpad_bottom": False,
            "trigger_left": 0.0,
            "trigger_right": 0.0
        }

    # ----------------------------
    # Controller input using Pygame
    # ----------------------------
    def read_gamepad_loop(self):
        if pygame.joystick.get_count() > 0:
            joy_name = pygame.joystick.Joystick(0).get_name()
            print(joy_name)
            if "xinput" in joy_name.lower(): # FIXME what about wired xbox controllers? is this even right????
                self.joystick = XboxOneController(0)
                print("starting xbox 1 controller")
            elif "xbox" in joy_name.lower():
                self.joystick = LinuxXboxOneController(0)
                print("starting linux xbox 1 controller")
            #TODO do other controller button bindings

            if self.joystick is not None:
                print(f"[Controller] Detected Joystick: {self.joystick.joy.get_name()}")
        else:
            print("[Controller] No joystick found with Pygame.")
            self.stop_event.set() # Stop the script if no controller

        while not self.stop_event.is_set():
            pygame.event.pump()

            if self.joystick:
                with self.lock:
                    s = self.controller_state
                    last_times = self.last_times.copy()
                    # Get Axis values (Sticks/Triggers)
                    try: 
                        s["left_stick_x"] = self.joystick.get_left_stick_x()
                        s["left_stick_y"] = -self.joystick.get_left_stick_y() 
                        s["right_stick_x"] = self.joystick.get_right_stick_x()
                        s["right_stick_y"] = -self.joystick.get_right_stick_y() 
                        s["trigger_left"] = self.joystick.get_trigger_left()
                        s["trigger_right"] = self.joystick.get_trigger_right()
                    except IndexError:
                        pass 

                    # Get Button values (mapping varies by OS/Controller)
                    s["button_a"], last_times["button_a"] = self.joystick.get_button_a(self.last_controller_state["button_a"], self.last_times["button_a"])
                    s["button_b"], last_times["button_b"] = self.joystick.get_button_b(self.last_controller_state["button_b"], self.last_times["button_b"])
                    s["button_x"], last_times["button_x"] = self.joystick.get_button_x(self.last_controller_state["button_x"], self.last_times["button_x"])
                    s["button_y"], last_times["button_y"] = self.joystick.get_button_y(self.last_controller_state["button_y"], self.last_times["button_y"])
                    s["button_left_bumper"], last_times["button_left_bumper"] = self.joystick.get_button_left_bumper(self.last_controller_state["button_left_bumper"], self.last_times["button_left_bumper"])
                    s["button_right_bumper"], last_times["button_right_bumper"] = self.joystick.get_button_right_bumper(self.last_controller_state["button_right_bumper"], self.last_times["button_right_bumper"])
                    s["button_center"], last_times["button_center"] = self.joystick.get_button_center(self.last_controller_state["button_center"], self.last_times["button_center"])
                    s["button_left"], last_times["button_left"] = self.joystick.get_button_left(self.last_controller_state["button_left"], self.last_times["button_left"])
                    s["button_right"], last_times["button_right"] = self.joystick.get_button_right(self.last_controller_state["button_right"], self.last_times["button_right"])
                    s["left_stick_button"], last_times["left_stick_button"] = self.joystick.get_left_stick_button(self.last_controller_state["left_stick_button"], self.last_times["left_stick_button"])
                    s["right_stick_button"], last_times["right_stick_button"] = self.joystick.get_right_stick_button(self.last_controller_state["right_stick_button"], self.last_times["right_stick_button"])

                    # Get DPad values (Hat/POV)
                    s["dpad_left"], last_times["dpad_left"] = self.joystick.get_dpad_left(self.last_controller_state["dpad_left"], self.last_times["dpad_left"])
                    s["dpad_right"], last_times["dpad_right"] = self.joystick.get_dpad_right(self.last_controller_state["dpad_right"], self.last_times["dpad_right"])
                    s["dpad_top"], last_times["dpad_top"] = self.joystick.get_dpad_top(self.last_controller_state["dpad_top"], self.last_times["dpad_top"])
                    s["dpad_bottom"], last_times["dpad_bottom"] = self.joystick.get_dpad_bottom(self.last_controller_state["dpad_bottom"], self.last_times["dpad_bottom"])

                    self.last_controller_state = s.copy()
                    self.last_times = last_times.copy()

                    # print debugging statement for figuring out actual button/axis numbers
                    # print()
                    # for key, value in s.items():
                    #     print(f"{key}: {value}")

            time.sleep(0.01) # 100 Hz update rate for polling

    # ----------------------------
    # Send loop
    # ----------------------------
    def send_loop(self):
        while not self.stop_event.is_set():
            if self.connected:
                with self.lock:
                    msg10 = self.controller_state.copy()

                    # print(self.controller_state["button_a"])
                    
                    msg = {
                        "sender": constants["CONTROLLER_INPUT_NAME"],
                        "destination": constants["ROBOT_NAME"],
                        "data": json.dumps(msg10)
                    }

                    try:
                        self.ws.send(json.dumps(msg))

                        # don't remove this debug statement you never know when you'll need to uncomment it... (unless the gui is working)
                        # print(f'{msg10["left_stick_x"]:0.2f} | {msg10["left_stick_y"]:0.2f} | {msg10["right_stick_x"]:0.2f} | {msg10["right_stick_y"]:0.2f} | {msg10["trigger_left"]:0.2f} | {msg10["trigger_right"]:0.2f}')
                    except Exception as e:
                        #FIXME
                        print(e)

            time.sleep(0.02) # 50 Hz

    # ----------------------------
    # Run client and shutdown handler
    # ----------------------------
    def shutdown_handler(self, sig, frame):
        print("\n[Controller] Shutting down...")

        #FIXME this doesn't work with CTRL+C well, doesn't shut down ever
        self.stop_event.set()
        self.ws.close()

    def run(self):
        # Start threads as DAEMONS
        t1 = threading.Thread(target=self.read_gamepad_loop, daemon=True)
        t2 = threading.Thread(target=self.send_loop, daemon=True)
        t1.start()
        t2.start()

        self.ws.run_forever(ping_interval=10, ping_timeout=5)
        print("[Controller] Exited cleanly")

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = "1" # necessary to process background events
    os.environ['SDL_JOYSTICK_RAWINPUT'] = "0" # necessary for bluetooth xbox controller to work
    os.environ['SDL_HINT_JOYSTICK_THREAD'] = "1" # necessary for xbox controller to not act like a mouse maybe?

    pygame.init()
    pygame.joystick.init()

    # window = pygame.display.set_mode([400, 400])
    # window.fill((0, 0, 0))

    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Robot] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    # client = ControllerClient(f"{url}:{port}")
    client = ControllerClient(f"ws://127.0.0.1:1909") #TODO FIXME is this supposed to be right?
    # we need to figure out if relay server is running on robot or on base station
    signal.signal(signal.SIGINT, client.shutdown_handler)
    try:
        client.run()
    except KeyboardInterrupt:
        print("[Controller] Keyboard interrupt caught in main.")
