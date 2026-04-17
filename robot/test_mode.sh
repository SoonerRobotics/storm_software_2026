echo "RUNNING TEST MODE"

echo "Activating venv..."
cd ~/Documents/storm_software_2026/robot
source ../venv/bin/activate

echo "running relay server"
gnome-terminal --command ../build/relay_server &

sleep 1

#TODO if we wanted to we could simply redirect all the output to a file instead of having to do logging
echo "Running processes..."
python3 ./robot.py &