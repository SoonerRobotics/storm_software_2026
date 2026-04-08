

# ---------- Camera sender client ----------
import base64
import json
import threading
import time
import cv2
import websocket
import tomllib

constants = {}

class CameraClient:
    def __init__(self, server_url, constants):
        self.server_url = server_url
        self.ws = None
        self.stop_event = threading.Event()
        self.connected = False

        self.constants = constants

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error
        )
        t = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 10, "ping_timeout": 5}, daemon=True)
        t.start()
        print(print(f"Starting camera WS thread with ID: {t.native_id}"))

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
            "id": 131,
            "ts": time.time(),
            "frame_b64": b64
        }

        envelope = {
            "sender": self.constants["DRIVER_CAMERA_NAME"],
            "destination": self.constants["GUI_NAME"],
            "data": json.dumps(payload)
        }

        if self.ws is not None:
            try:
                self.ws.send(json.dumps(envelope))
            except Exception as e:
                print(f"[Camera] send error: {e}")

    def shutdown(self):
        self.stop_event.set()
    
        if self.ws is not None:
            try:
                self.ws.close()
            except:
                pass

def camera_loop(cam_client: CameraClient):
    cap = cv2.VideoCapture(cam_client.constants["DRIVER_CAM_DEVICE_INDEX"])
    if not cap.isOpened():
        print("[Camera] Failed to open camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_client.constants["CAM_WIDTH"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_client.constants["CAM_HEIGHT"])
    cap.set(cv2.CAP_PROP_FPS, cam_client.constants["CAM_FPS"])

    period = 1.0 / cam_client.constants["CAM_FPS"]
    while not cam_client.stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Optional: downscale / compress more
        # frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        frame = cv2.rotate(frame, cv2.ROTATE_180)

        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        if ok:
            cam_client.send_frame(jpg.tobytes())

        time.sleep(period)

    cap.release()
    print("[Camera] Loop ended")

def main():
    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Robot] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    cam_client = CameraClient(f"{url}:{port}", constants)

    # Start camera WS connection & loop
    cam_client.connect()
    cam_thread = threading.Thread(target=camera_loop, args=(cam_client,), daemon=True)
    cam_thread.start()
    print(print(f"Starting camera thread with ID: {cam_thread.native_id}"))
    try:
        while not cam_client.stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt as e:
        pass
    finally:
        cam_client.shutdown()

if __name__ == "__main__":
    main()