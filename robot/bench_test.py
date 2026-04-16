# this file is meant to run from your computer, plugged directly into the Pico 2
# essentially acting as the robot and base station all in one

# import pygame
import struct
import serial
import time

def main():
    # init pygame
    # pygame.init()

    # open serial
    pico = serial.Serial("/dev/ttyACM0", 115200, timeout=0.5)

    # connect joystick
    # joystick = pygame.joystick.Joystick(0)
    # timer = pygame.time.Clock()

    # pygame events loop FIXME
    # for event in pygame.event.get():

    # our own event loop?
    try:
        while True:
            # get joystick input FIXME
            msg = struct.pack(
                ">c11Bc",
                b"$",
                # joystick.get_axis(0),
                # joystick.get_axis(1),
                # joystick.get_axis(2),
                # joystick.get_axis(3),
                127,
                127,
                127,
                127,
                127, # slide
                127, # intake
                127, # arm
                127, # wrist
                127, # claw
                127, # climber
                2, # jumpstart
                b"!"
            )

            # send serial message
            pico.write(msg)

            # don't overload
            time.sleep(1 / 50.0)
    finally:    
        # close serial
        pico.close()

if __name__ == "__main__":
    main()