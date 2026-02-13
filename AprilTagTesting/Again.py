from robotpy_apriltag import AprilTagDetector, AprilTagDetection, AprilTagPoseEstimator
import numpy as np
from scipy.spatial.transform import Rotation as R   
import cv2


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Check actual camera resolution
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"Camera resolution: {actual_width}x{actual_height}")
print(f"Calibration assumes cx={1169.3437}, cy={569.2571}")
print(f"This suggests calibration was done at ~2338x1138 resolution")
    
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
camera_params = [1516.0714382761676, 1482.655725687387, 990.2225656973194, 722.0443902530434]
tag_size = 0.0635  

estimate_config = AprilTagPoseEstimator.Config(tag_size, *camera_params)


estimator = AprilTagPoseEstimator(estimate_config)


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

    for result in results:
        pose = estimator.estimate(result)
        
        print("X(horizontal):" + str(pose.X() * 100) + "cm")
        print("Y(height):" + str(pose.Y() * 100) + "cm")
        print("Z(depth):" + str(pose.Z() * 100) + "cm")
        print(result.getId())
        #rot = R.from_matrix(pose.rotation())
        break

    cv2.imshow('frame', frame)

cap.release()
cv2.destroyAllWindows()