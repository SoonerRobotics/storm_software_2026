echo "[RUN ROBOT SCRIPT]"

echo "Activating venv..."
cd ~/Documents/storm_software_2026/robot
source ../venv/bin/activate

#TODO if we wanted to we could simply redirect all the output to a file instead of having to do logging
echo "Running processes..."
python3 ./robot.py &
python3 ./statistics.py &
python3 ./driver_camera.py &
python3 ./apriltag_camera.py