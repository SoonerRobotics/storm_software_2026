#TODO FIXME print version and stuff

#TODO FIXME have it install python and pip and cmake too? we should maybe check at least...
# sudo apt update
# sudo apt upgrade

echo "Running setup script in TODO: {CWD}..."

# install libhv for Tony's websocket server

# build Tony's websocket server
mkdir ./build
cmake -S ./src -B ./build
cmake --build ./build

# install python packages
# we should check which ones are installed and whatnot
# or honestly make a virtual environment
pip3 install opencv-python websocket-client #TODOFIXME