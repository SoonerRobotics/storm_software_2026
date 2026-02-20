import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R
from pyapriltags import Detector
import matplotlib.pyplot as plt

'''from pyapriltags import Detection, Detector
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import RigidTransform as T'''
import time

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
    
at_detector = Detector(families='tag36h11',
                        nthreads=1,
                        quad_decimate=1.0,
                        quad_sigma=0.0,
                        refine_edges=1,
                        decode_sharpening=0.25,
                        debug=0)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #Parameters: image to detect from, whether or not to estimate the position, camera calibration, AprilTag size
    camera_params = [1350.3598, 1345.6468, 1169.3437, 569.2571]
    tag_size = 0.1   
    results = at_detector.detect(gray, True, camera_params, tag_size)

    # Display the resulting frame
    if cv2.waitKey(1) == ord('q'):
        break

    for result in results:

        (corner_a, corner_b, corner_c, corner_d) = result.getCorners()

        corner_a = (int(corner_a[0]), int(corner_a[1]))
        corner_b = (int(corner_b[0]), int(corner_b[1]))
        corner_c = (int(corner_c[0]), int(corner_c[1]))
        corner_d = (int(corner_d[0]), int(corner_d[1]))

        line_color = (0, 255, 0) # green
        line_thickness = 5

    # Draw a rectangle using the corners
        cv2.line(frame, corner_a, corner_b, line_color, line_thickness)
        cv2.line(frame, corner_b, corner_c, line_color, line_thickness)
        cv2.line(frame, corner_c, corner_d, line_color, line_thickness)
        cv2.line(frame, corner_d, corner_a, line_color, line_thickness)
    
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 0, 255)
        thickness = 2
        frame = cv2.putText(frame, str(result.tag_id), corner_a, font, fontScale, color, thickness, cv2.LINE_AA)
        
        if result.pose_t is not None:
            t = result.pose_t.flatten()
            z = t[2] * 100  # Convert to centimeters
            x = t[0] * 100  # Convert to centimeters
            #print("X distance (cm):", x)
            #print("Z distance (cm):", z, end = '\n \n')
            print(f"  Translation (x, y, z): {t}")

            distance_cm = np.linalg.norm(t) * 100
            print(f"  Distance from camera: {distance_cm:.2f} centimeters")

            # Check if rotation matrix is valid before converting
            try:
                det = np.linalg.det(result.pose_R)
                if det > 0:  # Valid rotation matrix
                    # Try multiple conventions to see which matches your expected behavior
                    euler_xyz = R.from_matrix(result.pose_R).as_euler('xyz', degrees=True)
                    euler_zyx = R.from_matrix(result.pose_R).as_euler('ZYX', degrees=True)
                    
                    # The rotation about Y-axis (in camera frame) is typically what you perceive as left/right
                    angle_around_y = euler_zyx[1]  # Rotation around Y-axis
                    
                    #print(f"  XYZ convention - X: {euler_xyz[0]:.2f}°, Y: {euler_xyz[1]:.2f}°, Z: {euler_xyz[2]:.2f}°")
                    #print(f"  ZYX convention - Z: {euler_zyx[0]:.2f}°, Y: {euler_zyx[1]:.2f}°, X: {euler_zyx[2]:.2f}°")
                    #print(f"  Rotation around Y-axis (left/right): {angle_around_y:.2f}°")
                else:
                    print(f"  Invalid rotation matrix (det={det:.4f}), skipping orientation")
            except ValueError as e:
                print(f"  Could not compute orientation: {e}")
        else:
            print("No pose estimated (pose_t is None)")


    time.sleep(0.5)
    cv2.imshow('frame', frame)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()