
import json
import pygame
import time

from websockets.asyncio.client import connect

ROBOT_ADDRESS = "localhost" #TODO FIXME have this in another file???
ROBOT_PORT = 3333

joystick = None


async def main():
    pygame.joystick.init()

    #TODO FIXME even bother checking this?
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
    else:
        pass #TODO FIXME

    joystick = pygame.joystick.Joystick(0)

    stop = False

    async with connect(f"ws://{ROBOT_ADDRESS}:{ROBOT_PORT}") as websocket:
        while not stop:
            pygame.event.pump()

            if joystick is not None:
                state = {
                    "left_stick_x": joystick.get_axis(0),
                    "left_stick_y": joystick.get_axis(1),
                    "right_stick_x": joystick.get_axis(2),
                    "right_stick_y": joystick.get_axis(3),
                    "left_stick_button": joystick.get_button(0),
                    "right_stick_button": joystick.get_button(1),
                    "button_a": joystick.get_button(3),
                    "button_b": joystick.get_button(2),
                    "button_x": joystick.get_button(4),
                    "button_y": joystick.get_button(5),
                    "button_left_bumper": joystick.get_button(11),
                    "button_right_bumper": joystick.get_button(8),
                    "button_center": joystick.get_button(9),
                    "button_left": joystick.get_button(12),
                    "button_right": joystick.get_button(10),
                    "dpad_top": joystick.get_hat(0)[0] == -1,
                    "dpad_left": joystick.get_hat(0)[0] == 1,
                    "dpad_right": joystick.get_hat(0)[1] == 1,
                    "dpad_bottom": joystick.get_hat(0)[1] == -1,
                    "trigger_left": joystick.get_axis(4),
                    "trigger_right": joystick.get_axis(5)
                }

                await websocket.send(state)
            
            await asyncio.sleep(0)  # yield control to the event loop TODO FIXME?
            time.sleep(0.05) # 20 Hz TODO FIXME


if __name__ == "__main__":
    asyncio.run(main())