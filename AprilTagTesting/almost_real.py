from robotpy_apriltag import AprilTagDetector, AprilTagDetection, AprilTagPoseEstimator
import numpy as np
from scipy.spatial.transform import Rotation as R   
import cv2



cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# *** #
#This is all probably fine, probably keep as is unless we know for sure
at_detector = AprilTagDetector()
detect_config = AprilTagDetector.Config()

detect_config.decodeSharpening = 0.25
detect_config.refineEdges = 1
detect_config.quadDecimate = 1.0
detect_config.numThreads = 1
detect_config.debug = 0
detect_config.quadSigma = 0.0

at_detector.setConfig(detect_config)   
at_detector.addFamily('tag36h11')
# *** #

#camera calibration stuff, has been recalibrated very frequently so don't worry if numbers differ between files
camera_params = [1.389128301095909592e+03, 1.411771668458814474e+03, 1.023578058929374038e+03, 5.617593978785050695e+02] #Web cam
#camera_params = [1211.2034279937993, 1204.865899413857, 945.3223945388609, 557.9796530877504] #Global shutter
tag_size = 0.0635   #small
#tag_size = 0.1   #medium

estimate_config = AprilTagPoseEstimator.Config(tag_size, *camera_params)
estimator = AprilTagPoseEstimator(estimate_config)

tags_ID = []

poses_x = [0] * 12 #Empty space for poses
poses_z = [0] * 12

poses_rot_y = [0] * 12 #y is the only rotation we care about

def Estimate():
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        exit()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    
    results = at_detector.detect(gray)

    # Display the resulting frame
    if cv2.waitKey(1) == ord('q'):
        exit()
    
    tags_ID.clear()
    for i in range(len(results)):
        result = results[i]

        print(result.getId())
        pose = estimator.estimate(result)

        #x is horizontal z is depth
        poses_x[i] = pose.X() * 39.37008 #Convert to inches
        poses_z[i] = pose.Z() * 39.37008 / 1.2 #The 1.2 is a jerry rig, should probably fix later

        poses_rot_y[i] = -pose.rotation().y_degrees #negative because i want rotation to be clockwise positive

        tags_ID.append(result.getId())

        

    cv2.imshow('frame', frame)


def set_close():
    cap.release()
    cv2.destroyAllWindows()