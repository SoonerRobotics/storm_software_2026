echo "RUNNING BASE STATION"

# change directory
cd ~/Documents/storm_software_2026/base_station

# activate virtual environment
source ../venv/bin/activate

# run websocket relay
gnome-terminal --command ../build/relay_server &

sleep 1

# run python scripts
python3 ./controller_client.py &
python3 ./AprilTagPoses.py &
python3 ./storm_logging.py