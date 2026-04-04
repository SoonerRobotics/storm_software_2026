SERVER_URL = "ws://192.168.1.123:1909"

ROBOT_SENDER      = "3"   # robot control sender id
CONTROLLER_SENDER = "1"   # controller client id
CAM_SENDER        = "3_cam"
CAM_DESTINATION   = "4"   # UI / operator client id for video
GUI_SENDER        = "4"   #FIXME not sure if this is right?
APRILTAG_SENDER   = "3"   #FIXME?

# non-process-specific camera constants
DRIVER_CAM_DEVICE_INDEX = 0 # /dev/video0
APRILTAG_CAM_DEVICE_INDEX = 1 # /dev/video1