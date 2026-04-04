echo "Starting all robot processes..."

#TODO if we wanted to we could simply redirect all the output to a file instead of having to do logging
# and just base-station-side log the camera stream so we have videos. just a thought.
python3 ./robot.py &
python3 ./logging.py &
python3 ./driver_camera.py &
python3 ./AprilTagPoses.py &