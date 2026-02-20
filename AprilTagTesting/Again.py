from robotpy_apriltag import AprilTagDetector, AprilTagDetection, AprilTagPoseEstimator
import numpy as np
from scipy.spatial.transform import Rotation as R   
import cv2


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()


'''at_detector = AprilTagDetector(families='tag36h11',
                        nthreads=1,
                        quad_decimate=1.0,
                        quad_sigma=0.0,
                        refine_edges=1,
                        decode_sharpening=0.25,
                        debug=0)'''
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

#Parameters: image to detect from, whether or not to estimate the position, camera calibration, AprilTag size
camera_params = [1.389128301095909592e+03, 1.411771668458814474e+03, 1.023578058929374038e+03, 5.617593978785050695e+02] #Web cam
#camera_params = [1211.2034279937993, 1204.865899413857, 945.3223945388609, 557.9796530877504] #Global shutter
#tag_size = 0.0635   #small
tag_size = 0.1   #medium

estimate_config = AprilTagPoseEstimator.Config(tag_size, *camera_params)


estimator = AprilTagPoseEstimator(estimate_config)

poses_x = [0] * 12
poses_y = [0] * 12
poses_z = [0] * 12
poses_rot_x = [0] * 12
poses_rot_y = [0] * 12
poses_rot_z = [0] * 12
tags_ID = []

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
    
    '''poses_x.clear()
    poses_y.clear()
    poses_z.clear()
    poses_rot_x.clear()
    poses_rot_y.clear()
    poses_rot_z.clear()'''
    tags_ID.clear()
    for i in range(len(results)):
        result = results[i]

        print(result.getId())
        pose = estimator.estimate(result)
        poses_x[i] = pose.X() * 100
        poses_y[i] = pose.Y() * 100
        poses_z[i] = pose.Z() * 100
        poses_rot_x[i] = pose.rotation().x_degrees
        poses_rot_y[i] = pose.rotation().y_degrees
        poses_rot_z[i] = pose.rotation().z_degrees
        tags_ID.append(result.getId())
        '''print("X(horizontal):" + str(pose.X() * 100) + "cm")
        print("Y(height):" + str(pose.Y() * 100) + "cm")
        print("Z(depth):" + str(pose.Z() * 100) + "cm")
        print(result.getId())'''
        #rot = R.from_matrix(pose.rotation())
        

    cv2.imshow('frame', frame)



'''
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    
    results = at_detector.detect(gray)

    # Display the resulting frame
    if cv2.waitKey(1) == ord('q'):
        break
    i = 0
    for result in results:
        pose = estimator.estimate(result)
        poses_z.append(pose.Z() * 100)
        print("X(horizontal):" + str(pose.X() * 100) + "cm")
        print("Y(height):" + str(pose.Y() * 100) + "cm")
        print("Z(depth):" + str(pose.Z() * 100) + "cm")
        print(result.getId())
        #rot = R.from_matrix(pose.rotation())
        i+=1
        break

    cv2.imshow('frame', frame)
'''

def set_close():
    cap.release()
    cv2.destroyAllWindows()

