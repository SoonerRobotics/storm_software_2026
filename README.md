# storm_software_2026
Software for our 2026 [STORM](https://storm.soonerrobotics.org/) competition entry. You can view our design report submission [here]().
Additional information can be found on the [Sooner Competitive Robotics Wiki]().

{Insert Software block diagram}

# Dependencies
 - Boost, because of course you need Boost.
 - [libhv](https://github.com/ithewei/libhv) for websockets.

# Building
TODO: a setup script like for autonav's code would be useful here.

## Base Station Code
**NOTE:** this code is designed to run on a Linux environment. This can be on Windows Subsystem for Linux (WSL), although you might need to do some extra work to get controller input working.
~~1. Start by installing Boost, following steps 1 and 2 [here](https://www.boost.org/doc/libs/latest/more/getting_started/unix-variants.html). Make sure to unzip the tar file to `/usr/local/`~~
1. Install Boost by running `sudo apt install libboost-all-dev`.
2. Install libhv. From a suitable directory (~/Documents or ~/Downloads), run the following:
```sh
git clone https://github.com/ithewei/libhv.git
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

3. 

## Robot Code
This code is designed to run on a Raspberry Pi 5 running Ubuntu (? not Raspian?).
1. ???

## Firmware
1. Earl's Pico Library.
2. Profit.

# Running the code
TODO