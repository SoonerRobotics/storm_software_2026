# successor to autonav_statistics
# if this doesn't give meaningful data then we can just not run it

from dataclasses import dataclass
import threading
from typing import List
import websocket
import psutil
import tomllib
import json

constants = {}

@dataclass
class StatisticsMessage:
    cpu_percent: List[float] = [0.0]
    ram_percent: float = 0.0
    cpu_temperature: float = 0.0

class StatisticsClient:
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
        print("[Statistics] WS connected")
        self.connected = True

    def on_close(self, ws, code, reason):
        print("[Statistics] WS closed:", code, reason)
        self.connected = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Statistics] WS error:", error)

    def send_msg(self):
        if not self.connected:
            return
        
        payload = {
            "id": 170,
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory(),
            "cpu_temperature": psutil.sensors_temperatures()
        }

        envelope = {
            "sender": constants["STATISTICS_NAME"],
            "destination": constants["GUI_NAME"],
            "data": json.dumps(payload)
        }

        if self.ws is not None:
            try:
                self.ws.send(json.dumps(envelope))
            except Exception as e:
                print(f"[Statistics] send error: {e}")

    def shutdown(self):
        self.stop_event.set()
    
        if self.ws is not None:
            try:
                self.ws.close()
            except:
                pass

def main():
    with open("../constants.toml", "rb") as const_file:
        try:
            constants = tomllib.load(const_file)
        except Exception as e:
            print("[Robot] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    statistics = StatisticsClient(f"{url}:{port}")

    #FIXME do we need a while not stop event too?

if __name__ == "__main__":
    main()