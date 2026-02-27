import json
import time
import websocket
import threading
import signal
import pygame 

SERVER_URL = "ws://192.168.1.111:1909"
SENDER_NAME = "1"
DESTINATIONS = ["3"]

# ----------------------------
# Functions to send messages
# ----------------------------
def send_addressed(ws, dest, payload):
    msg = {
        "sender": SENDER_NAME,
        "destination": dest,
        "data": json.dumps(payload)
    }
    try:
        ws.send(json.dumps(msg))
    except Exception as e:
        pass

# ----------------------------
# Controller Client Class
# ----------------------------
class ControllerClient:

    # >> WebSocket callbacks (Moved above __init__ to fix AttributeError) <<
    def on_open(self, ws):
        print("[Controller] Connected to server")
        self.connected = True
        time.sleep(0.5) # Keep the delay for server timing
        msg11 = {"id": 11, "connection_status": True}
        for dest in DESTINATIONS:
            send_addressed(ws, dest, msg11)

    def on_close(self, ws, close_status_code, close_msg):
        print("[Controller] Disconnected from server")
        self.connected = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Controller] WebSocket error:", error)
        self.stop_event.set()

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
        self.joystick = None 

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
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[Controller] Detected Joystick: {self.joystick.get_name()}")
        else:
            print("[Controller] No joystick found with Pygame.")
            self.stop_event.set() # Stop the script if no controller

        while not self.stop_event.is_set():
            pygame.event.pump() 

            if self.joystick:
                with self.lock:
                    s = self.controller_state
                    # Get Axis values (Sticks/Triggers)
                    try: 
                        s["left_stick_x"] = self.joystick.get_axis(0)
                        s["left_stick_y"] = -self.joystick.get_axis(1) 
                        s["right_stick_x"] = self.joystick.get_axis(2)
                        s["right_stick_y"] = -self.joystick.get_axis(3) 
                        s["trigger_left"] = (self.joystick.get_axis(4) + 1) / 2 
                        s["trigger_right"] = (self.joystick.get_axis(5) + 1) / 2
                    except IndexError: pass 

                    # Get Button values (mapping varies by OS/Controller)
                    s["button_a"] = bool(self.joystick.get_button(0))
                    s["button_b"] = bool(self.joystick.get_button(1))
                    s["button_x"] = bool(self.joystick.get_button(3))
                    s["button_y"] = bool(self.joystick.get_button(2))
                    s["button_left_bumper"] = bool(self.joystick.get_button(4))
                    s["button_right_bumper"] = bool(self.joystick.get_button(5))
                    s["button_center"] = bool(self.joystick.get_button(11)) # Common mapping for center/mode
                    s["button_left"] = bool(self.joystick.get_button(8))   # Common mapping for select
                    s["button_right"] = bool(self.joystick.get_button(9))  # Common mapping for start
                    s["left_stick_button"] = bool(self.joystick.get_button(12))
                    s["right_stick_button"] = bool(self.joystick.get_button(10))

                    # Get DPad values (Hat/POV)
                    hat = self.joystick.get_hat(0)
                    s["dpad_left"] = (hat[0] == -1)
                    s["dpad_right"] = (hat[0] == 1)
                    s["dpad_top"] = (hat[1] == 1)
                    s["dpad_bottom"] = (hat[1] == -1)

            time.sleep(0.01) # 100 Hz update rate for polling

    # ----------------------------
    # Send loop
    # ----------------------------
    def send_loop(self):
        while not self.stop_event.is_set():
            if self.connected:
                with self.lock:
                    msg10 = self.controller_state.copy()
                    for dest in DESTINATIONS:
                        send_addressed(self.ws, dest, msg10)
            time.sleep(0.02) # 50 Hz

    # ----------------------------
    # Run client and shutdown handler
    # ----------------------------
    def shutdown_handler(self, sig, frame):
        print("\n[Controller] Shutting down...")
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
    client = ControllerClient(SERVER_URL)
    signal.signal(signal.SIGINT, client.shutdown_handler)
    try:
        client.run()
    except KeyboardInterrupt:
        print("[Controller] Keyboard interrupt caught in main.")
