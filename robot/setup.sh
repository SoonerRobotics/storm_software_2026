#TODO FIXME print version and stuff

#TODO FIXME have it install python and pip and cmake too? we should maybe check at least...
# sudo apt update
# sudo apt upgrade

echo "Running setup script in TODO: {CWD}..."

# install libhv for Tony's websocket server
echo "Installing libhv..."
#TODO

# build Tony's websocket server
echo "Building libhv..."
mkdir ./build
cmake -S ./src -B ./build
cmake --build ./build

# install python packages
echo "Activating virtual environment..."
#TODO

# we should check which ones are installed and whatnot
# or honestly make a virtual environment
echo "Installing python packages..."
pip3 install opencv-python websocket-client #TODOFIXME