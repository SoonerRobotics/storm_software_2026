echo "RUNNING BASE STATION SETUP"

# install necessary packages
# echo "Installing packages..."
# apt update
# apt install cmake build-essential python3.12-venv #FIXME???
# can't sudo this because like... need to change to HOME and stuff

# assumes you already have python

# change directoriess
cd ~/Documents

# download libhv
echo "Downloading libhv..."
git clone https://github.com/ithewei/libhv.git

# install libhv
echo "Installing libhv..."

cd libhv
mkdir build
cd build

cmake ..
cmake --build .

# install python dependencies
echo "Installing python packages..."
pip3 install opencv-python websocket-client pygame psutil robotpy-apriltag scipy