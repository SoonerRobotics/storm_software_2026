#TODO listen to all messages and log them? this might belong more on the base station...
# yeah should run on the base station, the pi will have its hands full with the 2 camera streams

import websocket
import tomllib
import json
import csv
import cv2
import threading
import psutil

constants = {}

class LoggingClient:
    def __init__(self, server_url):
        self.ws = websocket.WebSocketApp(
            server_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )

        self.filename = "" #FIXME default filename... where do we want files to go?

        self.t = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 1, "ping_timeout": 0.5}, daemon=True)
        self.t.start()
    
    def on_open(self, ws):
        print("[Logging] Logging WS connected")

        #FIXME we may have to do like, some funky send_all("destination: logger") or something...

    def on_message(self, ws, raw):
        #FIXME we might need a Lock()
        try:
            msg = json.loads(json.load(raw)["data"])

            if msg["id"] == 30:
                # if it's a like, "start match" message we should start a new file
                # filename is like, date and time .csv
                pass
            elif msg["id"] == camera:
                pass
                # except! for videos... copy the code from autonav_logging.py from 2025
            else:
                # just throw all the messages in there
                #TODO FIXME
                print(msg)
            
            #TODO also log like, CPU and RAM percentage of base station


        except Exception as e:
            print(f"[Logging] WS message error: {e}")
    
    def on_close(self, ws, code, reason):
        #FIXME we might need a stop_event() like in controller_client
        print("[Logging] WS closed:", code, reason)
    
    def on_error(self, ws, error):
        print(f"[Logging] WS error: {error}")

def main():
    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Logging] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"] #FIXME this might need to be localhost if running on the robot...?

    logger = LoggingClient(f"{url}:{port}")