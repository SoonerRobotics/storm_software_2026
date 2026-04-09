#TODO listen to all messages and log them? this might belong more on the base station...
# yeah should run on the base station, the pi will have its hands full with the 2 camera streams

import websocket
import tomllib
import json
import csv
import cv2
import threading
import psutil
import time
import os
import base64

constants = {}

class LoggingClient:
    def __init__(self, server_url, log_path_prefix):
        self.ws = websocket.WebSocketApp(
            server_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )

        self.log_path_prefix = log_path_prefix #FIXME do we want/need to do some os.path.join() or something?
        self.filename = ""
        self.file = None
        self.writer = None
        self.video_writer = None
        #FIXME do we need a lock?

        self.stop_event = threading.Event()

        self.t = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 1, "ping_timeout": 0.5}, daemon=True)
        self.t.start()
        print(f"[Logging] Starting thread with ID {self.t.native_id}")

    
    def on_open(self, ws):
        print("[Logging] Logging WS connected")

        #FIXME we may have to do like, some funky send_all("destination: logger") or something...

    def on_message(self, ws, raw):
        #FIXME we might need a Lock()
        try:
            #FIXME get timestamp too? for logging???
            msg = json.loads(json.load(raw)["data"])

            match (msg["id"]):
                case 30:
                    # if it's a like, "start match" message we should start a new file
                    # filename is like, date and time .csv
                    # os.makedirs(self.filename) #????
                    pass
                case 31:
                    # match start message, one field "timestamp" unsigned long for the start of the match?
                    pass

                case 131: # driver camera
                    if self.video_writer is None:
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')

                        self.video_writer = cv2.VideoWriter(f"{self.log_path_prefix}temp_{time.time()}.avi", fourcc, constants["CAM_FPS"], (constants["CAM_WIDTH"], constants["CAM_HEIGHT"]))

                        encoded = base64.b64decode(msg["frame_b64"])
                        frame = cv2.imdecode(encoded)

                        self.video_writer.write(frame)
        
                
                case _:
                    # to handle if there is no GUI
                    if self.file is None:
                        self.file = open(f"{self.log_path_prefix}temp_{time.time()}.csv", "at", newline='')
                    
                    if self.writer is None:
                        self.writer = csv.writer(self.file)



                    # just throw all the messages in there FIXME?
                    self.writer.writerow(msg) #??? msg.values()? msg.keys()? dir(msg)? dict(msg)?
            
            #TODO also log like, CPU and RAM percentage of base station?


        except Exception as e:
            print(f"[Logging] WS message error: {e}")
    
    def on_close(self, ws, code, reason):
        #FIXME we might need a stop_event() like in controller_client
        print("[Logging] WS closed:", code, reason)
        if self.file is not None:
            self.file.close()

            self.file = None
            self.writer = None
        
        self.stop_event.set()
    
    def on_error(self, ws, error):
        print(f"[Logging] WS error: {error}")

    def shutdown(self):
        self.on_close(self.ws, "", "keyboard interrupt")

def main():
    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Logging] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"] #FIXME this might need to be localhost if running on the robot...?

    logger = LoggingClient(f"{url}:{port}", constants["LOGGING_PATH"])

    try:
        while not logger.stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt as e:
        pass
    finally:
        logger.shutdown()

if __name__ == "__main__":
    main()