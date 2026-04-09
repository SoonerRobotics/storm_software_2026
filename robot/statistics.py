# successor to autonav_statistics
# if this doesn't give meaningful data then we can just not run it

from dataclasses import dataclass
import threading
from typing import List
import websocket
import psutil
import tomllib
import json
import time

constants = {}

@dataclass
class StatisticsMessage:
    cpu_percent: float = 0.0
    cpu_frequency: float = 0.0
    ram_percent: float = 0.0
    temperature: float = 0.0

class StatisticsClient:
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
        print(f"[Statistics] Starting statistics WS thread with ID {t.native_id}")

    def on_open(self, ws):
        print("[Statistics] WS connected")
        self.connected = True

    def on_close(self, ws, code, reason):
        print("[Statistics] WS closed:", code, reason)
        self.connected = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[Statistics] WS error:", error)

    def run_forever(self):
        while not self.stop_event.is_set():
            if not self.connected:
                time.sleep(1)
                continue
            
            payload = {
                "id": 170,
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(0.0, False),
                "cpu_frequency": f"{psutil.cpu_freq(False).current/1000:.3f}",
                "ram_percent": psutil.virtual_memory().percent,
                "temperature": psutil.sensors_temperatures()["coretemp"][0][1] #FIXME I have no idea if this is the right one
            }

            envelope = {
                "sender": self.constants["STATISTICS_NAME"],
                "destination": self.constants["GUI_NAME"],
                "data": json.dumps(payload)
            }            

            if self.ws is not None:
                try:
                    self.ws.send(json.dumps(envelope))
                except Exception as e:
                    print(f"[Statistics] send error: {e}")
            
            time.sleep(self.constants["STATISTICS_UPDATE_INTERVAL"])

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
            print("[Statistics] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    statistics = StatisticsClient(f"{url}:{port}", constants)
    statistics.connect()
    statistics_thread = threading.Thread(target=statistics.run_forever, daemon=True)
    statistics_thread.start()
    print(print(f"Starting statistics thread with ID: {statistics_thread.native_id}"))
    
    try:
        while not statistics.stop_event.is_set():
            time.sleep(1) #FIXME is this a good number?
    except KeyboardInterrupt as e:
        pass #FIXME?
    finally:
        statistics.shutdown()

if __name__ == "__main__":
    main()