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
