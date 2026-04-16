# storm_software_2026
Software for *Pink Blush*, our 2026 [STORM](https://storm.soonerrobotics.org/) competition entry. More information about the software architecture and implementation can be found in the Design Report and Software Architecture documents on the [SCR Wiki](wiki.soonerrobotics.org/books/2025-2026-J3g). You will need a C++ compiler (the default gcc is probably fine) to build part of the code, and Python 3 to run the other part.

# Building
There are setup scripts in both the `base_station` and `robot` directories for installing packages required to build and run the robot code, but they are incomplete and do not work at time of writing. To build the code for the base station and robot, you will need to install libhv:
 1. (from a directory above) `git clone https://github.com/ithewei/libhv.git`
 2. ```
    cd libhv
    mkdir build
    cd build

    cmake ..
    cmake --build .
    ```
 3. You made need to `sudo make install` as well

Then install the Python packages:
 1. `python3 -m venv ./venv`
 2. `source ./venv/bin/activate`
 3. `pip3 install opencv-python websocket-client pygame psutil robotpy-apriltag scipy`

Then at last build Tony's websocket relay server:
 1. `mkdir ./build`
 2. `cmake -S ./ws_server/src -B ./build`
 3. `cmake --build ./build`

# Running the code
There are two ways to run the robot code, competition mode and test mode. Competition mode runs the Base Station code on a separate laptop from the Robot code. Test mode is intended for outreach events and only runs code on the robot. The Base Station is the laptop that the gamepad is connected to, and the Robot is the actual Rasperry Pi on the robot. To start the Base Station, `cd base_station` and `./run_base_station.sh`. You may need to `sudo chmod +x ./run_base_station.sh` if it gives you a permission denied error. After the Base Station has been started, on the robot, `cd robot` and `./run_robot.sh`. To view the GUI you will need to refresh the GUI html file so the websocket server can identify where to send GUI messages to.

To run the robot in test mode, simply connect a gamepad to the robot and go! The `test_mode.sh` script should automatically run on startup. You can set up this behavior by following these steps:
{TODO}
You can disable this behavior (to run the actual robot code) by following these steps:
{TODO}

# Button Bindings
The default button bindings are as below:
{TODO}
If you are not using a bluetooth XBox One controller, you may need to add it to `controller_client.py`. Simply copy the `LinuxXboxOneController` class and change the button and axes IDs to match what your controller returns, then add it to the if/elif chain in `read_gamepad_loop` on line 234.

# Constants
*Pink Blush*'s code is highly configurable. Many different values can be editing without having to dig in the code, in the `constants.toml` file. A guide to TOML can be found [here](https://toml.io/en/). You will need to edit COMPETITION_SERVER_URL and change it to point to the IP of the robot. The port does not need to be changed, since it is hard-coded in `relay_server.cpp`, but if you changed it there then you should change it in `constants.toml`. The serial port of the Pico should default to `/dev/ttyACM0` on Linux. If not, update the `SERIAL_PORT` constant. You may also need to change the driver and apriltag camera device indices.

## Viewing the GUI
If you want to view the GUI on a separate device from the Base Station, you will need to edit {THE IP ADDRESS}

# Firmware
The robot runs off a single [Raspberry Pi Pico 2](https://wiki.soonerrobotics.org/books/firmware-development/page/raspberry-pi-pico-2). You will need the Arduino IDE, and install the following libraries:
 * Adafruit DS3502
 * Adafruit NeoPixel
 * RPI_PICO_TimerInterrupt
 * Adafruit BusIO
 * [Earl's arduino-pico library](https://github.com/earlephilhower/arduino-pico)

## TODO List
 * add WS reconnection logic to fix the `ping/pong timeout` errors we kept getting at competition
 * find a way to reduce bandwidth
 * get Tony's WebRTC camera streaming code working
 * add test mode
 * add gamepad reconnection logic
 * fix apriltag autoalignment
 * run apriltag detection on the robot
 * add sequences
 * make actual autonomous programs