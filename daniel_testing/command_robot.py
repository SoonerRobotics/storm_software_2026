import asyncio

from websockets.sync.client import connect

from daniel_testing.command_framework import Action, ActionScheduler, Joystick, Trigger


BASE_STATION_ADDRESS = "http://127.0.0.1" #TODO port and actual address
BASE_STATION_PORT = 3333

APRILTAG_ADDRESS = "http://127.0.0.1" #TODO port and actual address (this one can be localhost though I think)
APRILTAG_PORT = 3334 #TODO FIXME

async def main():
    scheduler = ActionScheduler()

    # set up buttons
    joystick = Joystick()

    aButton = Trigger(scheduler)
    bButton = Trigger(scheduler)
    xButton = Trigger(scheduler)
    yButton = Trigger(scheduler)
    leftBumper = Trigger(scheduler)
    rightBumper = Trigger(scheduler)

    #TODO FIXME ???
    driveAction = Action(callback, -1)

    autonomous_programs = []
    autonomous_index = -1 #TODO FIXME we should have a default though

    

    # on message recieved

    # with connect(BASE_STATION_ADDRESS) as base_station:
    #     async def robot_loop():

    #     async for message in base_station:
    #         await robot_loop(message)

    # consumer_task = asyncio.create_task(consumer_handler(websocket))
    # producer_task = asyncio.create_task(producer_handler(websocket))
    # done, pending = await asyncio.wait(
    #     [consumer_task, producer_task],
    #     return_when=asyncio.FIRST_COMPLETED,
    # )
    # for task in pending:
    #     task.cancel()

    # with connect(APRILTAG_ADDRESS) as apriltags:
    #     #TODO FIXME
    #     pass


if __name__ == "__main__":
    asyncio.run(main())

    #TODO FIXME try/catch???