import cv2
from pyapriltags import Detection, Detector
from scipy.spatial.transform import Rotation as R
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

i = 0
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
    results = at_detector.detect(gray, True, [1398.92, 1398.92, 967.614, 570.073], 0.1)

    # Display the resulting frame
    if cv2.waitKey(1) == ord('q'):
        break

    for result in results:
        #print(result.tag_id)
        i += 1
        (corner_a, corner_b, corner_c, corner_d) = result.corners

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
        #Translation vector output:
        #[horizontal translation (maybe?)
        #vertical translation
        #depth translation]
        #print(result.pose_t)


        #result.pose_R is a rotation matrix (needs to be turned into real numbers)
        if(i == 10):
            rotation = R.from_matrix(result.pose_R)
            print(rotation.as_euler("zxy", True))
            i = 0

    cv2.imshow('frame', frame)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()