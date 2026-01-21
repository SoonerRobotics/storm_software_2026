import json
import time
import websocket
import threading
import signal
import pygame 

SERVER_URL = "ws://192.168.1.123:1909"
SENDER_NAME = "1"
DESTINATIONS = ["3"]

DEADZONE = 0.05  # deadzone for analog sticks/triggers

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
        # Log once per failure site instead of silent pass
        print(f"[Controller] Error sending to {dest}: {e}")

# ----------------------------
# Utility: apply deadzone
# ----------------------------
def apply_deadzone(value, dz=DEADZONE):
    if abs(value) < dz:
        return 0.0
    return value

# ----------------------------
# Controller Client Class
# ----------------------------
class ControllerClient:

    # ----------------------------
    # WebSocket callbacks
    # ----------------------------
    def on_open(self, ws):
        print("[Controller] Connected to server")
        self.connected = True
        time.sleep(0.5)  # Keep delay for server timing
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

    # ----------------------------
    # Initialize
    # ----------------------------
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
        self.mapping = {}

    # ----------------------------
    # Default controller state
    # ----------------------------
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
    # Controller input loop (auto-mapping)
    # ----------------------------
    def read_gamepad_loop(self):
        pygame.init()
        pygame.joystick.quit()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("[Controller] No joystick found.")
            self.stop_event.set()
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        name = self.joystick.get_name()
        print(f"[Controller] Detected joystick: {name}")

        # Automatic mapping for Xbox, PlayStation, generic
        if "xbox" in name.lower():
            mapping = {
                "button_a": 0,
                "button_b": 1,
                "button_x": 3,
                "button_y": 4,
                "button_left_bumper": 6,
                "button_right_bumper": 7,
                "button_left": 10,
                "button_right": 11,
                "button_center": 12,
                "left_stick_button": 13,
                "right_stick_button": 14,
                "dpad": 0,
                "axes": {
                    "left_stick_x": 0,
                    "left_stick_y": 1,
                    "right_stick_x": 2,
                    "right_stick_y": 3,
                    "trigger_left": 5,
                    "trigger_right": 4
                }
            }
        elif "playstation" in name.lower() or "dualshock" in name.lower() or "dual sense" in name.lower():
            mapping = {
                "button_a": 0,  # Cross
                "button_b": 1,  # Circle
                "button_x": 2,  # Square
                "button_y": 3,  # Triangle
                "button_left_bumper": 4,
                "button_right_bumper": 5,
                "button_left": 8,   # Share
                "button_right": 9,  # Options
                "button_center": 12, # PS button
                "left_stick_button": 10,
                "right_stick_button": 11,
                "dpad": 0,
                "axes": {
                    "left_stick_x": 0,
                    "left_stick_y": 1,
                    "right_stick_x": 2,
                    "right_stick_y": 3,
                    "trigger_left": 4,
                    "trigger_right": 5
                }
            }
        else:
            print("[Controller] Unknown controller, using default mapping")
            mapping = {
                "button_a": 0,
                "button_b": 1,
                "button_x": 3,
                "button_y": 2,
                "button_left_bumper": 4,
                "button_right_bumper": 5,
                "button_left": 8,
                "button_right": 9,
                "button_center": 10,
                "left_stick_button": 11,
                "right_stick_button": 12,
                "dpad": 0,
                "axes": {
                    "left_stick_x": 0,
                    "left_stick_y": 1,
                    "right_stick_x": 3,
                    "right_stick_y": 4,
                    "trigger_left": 2,
                    "trigger_right": 5
                }
            }

        self.mapping = mapping

        while not self.stop_event.is_set():
            pygame.event.pump()
            axes = mapping["axes"]

            with self.lock:
                s = self.controller_state

                # Axes
                try:
                    lx = self.joystick.get_axis(axes["left_stick_x"])
                    ly = -self.joystick.get_axis(axes["left_stick_y"])
                    rx = self.joystick.get_axis(axes["right_stick_x"])
                    ry = -self.joystick.get_axis(axes["right_stick_y"])
                    tl = (self.joystick.get_axis(axes["trigger_left"]) + 1) / 2
                    tr = (self.joystick.get_axis(axes["trigger_right"]) + 1) / 2

                    # Apply deadzone
                    s["left_stick_x"] = apply_deadzone(lx)
                    s["left_stick_y"] = apply_deadzone(ly)
                    s["right_stick_x"] = apply_deadzone(rx)
                    s["right_stick_y"] = apply_deadzone(ry)
                    s["trigger_left"] = apply_deadzone(tl)
                    s["trigger_right"] = apply_deadzone(tr)

                except Exception as e:
                    print(f"[Controller] Axis read error: {e}")

                # Buttons
                for btn_name in [
                    "button_a","button_b","button_x","button_y",
                    "button_left_bumper","button_right_bumper",
                    "button_left","button_right","button_center",
                    "left_stick_button","right_stick_button"
                ]:
                    try:
                        s[btn_name] = bool(self.joystick.get_button(mapping[btn_name]))
                    except Exception:
                        s[btn_name] = False

                # DPad (hat)
                try:
                    hat = self.joystick.get_hat(mapping["dpad"])
                    s["dpad_left"] = (hat[0] == -1)
                    s["dpad_right"] = (hat[0] == 1)
                    s["dpad_top"] = (hat[1] == 1)
                    s["dpad_bottom"] = (hat[1] == -1)
                except Exception:
                    s["dpad_left"] = s["dpad_right"] = s["dpad_top"] = s["dpad_bottom"] = False

            time.sleep(0.01)

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
    # Shutdown handler
    # ----------------------------
    def shutdown_handler(self, sig, frame):
        print("\n[Controller] Shutting down...")
        self.stop_event.set()
        self.ws.close()

    # ----------------------------
    # Run client
    # ----------------------------
    def run(self):
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

