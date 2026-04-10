from typing import List

from robotpy_apriltag import AprilTagDetector, AprilTagDetection, AprilTagPoseEstimator
import numpy as np
from scipy.spatial.transform import Rotation as R   
import cv2
import json
import time
import threading
import websocket
import tomllib
import base64

constants = {}

class AprilTagClient:
    def __init__(self, server_url, constants):
        self.server_url = server_url
        self.ws = None
        self.stop_event = threading.Event()
        self.connected = False

        self.constants = constants
        self.field = json.load(open(constants["APRILTAG_JSON_PATH"]))

        # lots of configuration stuff
        self.at_detector = AprilTagDetector()

        #FIXME add to constants file? honestly if we aren't changing it frequently then it doesn't really matter...
        detect_config = AprilTagDetector.Config()
        detect_config.decodeSharpening = 0.25
        detect_config.refineEdges = 1
        detect_config.quadDecimate = 1.0
        detect_config.numThreads = 1
        detect_config.debug = 0
        detect_config.quadSigma = 0.0
        
        self.at_detector.setConfig(detect_config)   
        self.at_detector.addFamily('tag36h11')

        #camera calibration stuff, has been recalibrated very frequently so don't worry if numbers differ between files
        #camera_params = [1.389128301095909592e+03, 1.411771668458814474e+03, 1.023578058929374038e+03, 5.617593978785050695e+02] #Web cam
        #camera_params = [1709.8645603523432, 1689.1037121536826, 730.0106844229263, 493.8146502035437] #Brendan Camera
        camera_params = [1211.2034279937993, 1204.865899413857, 945.3223945388609, 557.9796530877504] #Global shutter
        tag_size = 0.0635   #small
        #tag_size = 0.1   #medium

        estimate_config = AprilTagPoseEstimator.Config(tag_size, *camera_params)
        self.estimator = AprilTagPoseEstimator(estimate_config)


    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error,
            on_message=self.on_message
        )
        t = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 10, "ping_timeout": 5}, daemon=True)
        t.start()
        print(print(f"Starting apriltag WS thread with ID: {t.native_id}"))

    def on_open(self, ws):
        print("[AprilTag] WS connected")
        self.connected = True

        # let the relay server know where we are
        ws.send(json.dumps({
            "sender": self.constants["APRILTAG_NAME"],
            "destination": self.constants["ROBOT_NAME"],
            "data": "{}"
        }))


    def on_close(self, ws, code, reason):
        print("[AprilTag] WS closed:", code, reason)
        self.connected = False
        self.stop_event.set()

    def on_error(self, ws, error):
        print("[AprilTag] WS error:", error)

    def on_message(self, ws, raw):
        if not self.connected:
            return

        msg = json.loads(raw)
        if msg.get("destination") != self.constants["APRILTAG_NAME"]:
            return

        if msg.get("sender") != self.constants["APRILTAG_CAMERA_NAME"]:
            return
        
        payload = json.loads(msg["data"])
        if payload.get("id") != 131:
            return

        encoded = payload.get("frame_b64")
        if not encoded:
            return

        tags_ID = []
        poses_x = [0] * 12 # Empty space for poses
        poses_z = [0] * 12
        poses_rot_y = [0] * 12  #y is the only rotation we care about

        # decode camera frame
        mat = np.frombuffer(base64.b64decode(encoded), np.uint8)
        frame = cv2.imdecode(mat, cv2.IMREAD_GRAYSCALE)
        if frame is None:
            return

        # Our operations on the frame come here
        results = self.at_detector.detect(frame)
        
        tags_ID.clear()
        for idx, result in enumerate(results):
            pose = self.estimator.estimate(result)

            # x is horizontal z is depth
            poses_x[idx] = pose.X() * 39.37008 # Convert to inches
            poses_z[idx] = pose.Z() * 39.37008 / 1.2 # The 1.2 is a jerry rig, should probably fix later

            poses_rot_y[idx] = -pose.rotation().y_degrees # negative because I want rotation to be clockwise positive

            tags_ID.append(result.getId())
        cv2.imshow("frame", frame)
        cv2.waitKey(1)

        tag_to_use = 0

        curr_local_x = 0.0
        curr_local_y = 0.0
        curr_rotation = 0.0
        
        tag_rot = 700
        for i in range(len(tags_ID)):

            #placeholder for loop
            if poses_rot_y[i] < tag_rot:
                tag_to_use = i

            # field rotation of the tag
            tag_rot = self.field["tags"][tags_ID[tag_to_use]]["pose"]["rotation"]

            if tag_rot == 0:
                curr_local_x += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["x"] - poses_x[tag_to_use]
                curr_local_y += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["y"] - poses_z[tag_to_use]

            elif tag_rot == 90:
                curr_local_x += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["x"] - poses_z[tag_to_use]
                curr_local_y += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["y"] + poses_x[tag_to_use]

            elif tag_rot == 180:
                curr_local_x += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["x"] + poses_x[tag_to_use]
                curr_local_y += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["y"] + poses_z[tag_to_use]

            elif tag_rot == 270:
                curr_local_x += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["x"] + poses_z[tag_to_use]
                curr_local_y += self.field["tags"][tags_ID[tag_to_use]]["pose"]["translation"]["y"] - poses_x[tag_to_use]
            else:
                continue

        if tag_rot == 700:
            return
        
        curr_rotation = tag_rot + poses_rot_y[tag_to_use]
        if curr_rotation < 0:
            curr_rotation += 360
        
        payload = {
            "id": 141,
            "ts": time.time(),
            "ids": tags_ID[tag_to_use],
            "x": curr_local_x,
            "y": curr_local_y,
            "heading": curr_rotation,
            "x_diff": poses_x[tag_to_use] - 3, #3 is for camera offset from center ish, should prob actually measure
            "y_diff": poses_z[tag_to_use], 
            "rot": poses_rot_y[tag_to_use]
        }

        print(payload)

        envelope = {
            "sender": self.constants["APRILTAG_NAME"],
            "destination": self.constants["GUI_NAME"], #FIXME we should send to the robot as well
            "data": json.dumps(payload)
        }

        if self.ws is not None:
            try:
                self.ws.send(json.dumps(envelope))
            except Exception as e:
                print(f"[AprilTag] send error: {e}")

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
            print("[AprilTag] Failed to read constants file")
            raise SystemExit
    
    url = constants["COMPETITION_SERVER_URL"] if constants["COMPETITION"] else constants["LOCAL_SERVER_URL"]
    port = constants["COMPETITION_SERVER_PORT"] if constants["COMPETITION"] else constants["LOCAL_SERVER_PORT"]

    apriltag_client = AprilTagClient(f"{url}:{port}", constants)

    apriltag_client.connect()
    
    # Start camera WS connection & loop
    try:
        while not apriltag_client.stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt as e:
        pass
    finally:
        apriltag_client.shutdown()

if __name__ == "__main__":
    main()
