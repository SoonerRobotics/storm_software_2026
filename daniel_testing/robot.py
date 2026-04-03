
from statemachine.contrib.diagram import DotGraphMachine
from statemachine import State, StateChart


ROBOT_ADDRESS = "localhost" #TODO FIXME have this in another file???
ROBOT_PORT = 3333

class Robot(StateChart):
    OFF = State(initial=True)
    AUTONOMOUS = State()
    TELEOP = State()

    OFF.to(AUTONOMOUS)
    AUTONOMOUS.to(TELEOP)

    def on_autonomous(self):
        pass #TODO FIXME

    def on_teleop(self):
        pass #TODO FIXME


class Intake(StateChart):
    OFF = State(initial=True)
    INTAKING = State()
    OUTTAKING = State()

    intake = INTAKING.from_(OUTTAKING, OFF)
    outtaking = OUTTAKING.from_(INTAKING, OFF)
    off = OFF.from_(INTAKING, OUTTAKING)

    #TODO FIXME other stuff???? add autonomous states????

    def on_intake(self):
        #TODO FIXME
        pass


class Drivetrain(StateChart):
    OFF = State(initial=True)
    
    DRIVING_TIMED = State()
    TURNING_TIMED = State()
    
    TELEOP = State()
    LINING_UP = State()

    lining_up = LINING_UP.from_(TELEOP, DRIVING_TIMED, TURNING_TIMED, OFF)

    driving_autonomous = DRIVING_TIMED.from_(TURNING_TIMED, TELEOP, LINING_UP, OFF)
    turning_autonomous = TURNING_TIMED.from_(DRIVING_TIMED, TELEOP, LINING_UP, OFF)

    driving_teleop = TELEOP.from_(DRIVING_TIMED, TURNING_TIMED, OFF, LINING_UP)


class Scorer(StateChart):
    OFF = State(initial=True)

    RESTING = State()
    PICKING_UP_BATTERY = State()

    SCORING_LOW = State()
    SCORING_HIGH = State()

    #TODO FIXME what about left/right?

    start_match = OFF.to(RESTING)

    holding_battery = PICKING_UP_BATTERY.to(RESTING)

    prepare_to_pick_up = RESTING.to(PICKING_UP_BATTERY)
    
    raise_to_score_low = RESTING.to(SCORING_LOW)

    raise_to_score_high = RESTING.to(SCORING_HIGH)
    raise_a_little = SCORING_LOW.to(SCORING_HIGH)

    lower_to_score_low = SCORING_HIGH.to(SCORING_LOW)

    stop_scoring_high = SCORING_HIGH.to(RESTING)
    stop_scoring_low = SCORING_LOW.to(RESTING)

    def on_start_match(self):
        # clamp claw to hold battery
        # reel linear slide in
        # keep arm at middle height
        pass

    def on_prepare_to_pick_up(self):
        # open claw
        # bring arm to down position
        # something with slide?
        pass

    def on_holding_battery(self):
        # close claw
        # slide in?
        # bring arm up to resting position
        pass

    def on_raise_to_score_low(self):
        pass #TODO FIXME

    def on_raise_to_score_high(self):
        pass #TODO FIXME

    def on_raise_a_little(self):
        pass #TODO FIXME

    def on_lower_to_score_low(self):
        pass #TODO FIXME

    def on_stop_scoring_high(self):
        pass #TODO FIXME

    def on_stop_scoring_low(self):
        pass #TODO FIXME



async def main():
    async def handler(websocket):
        robot = Robot()
        drivetrain = Drivetrain()
        intake = Intake()
        scorer = Scorer()

        while True:
            message = await websocket.recv()
            print(message) #TODO FIXME

            await asyncio.sleep(0)  # yield control to the event loop

            #TODO FIXME 

    async with serve(handler, ROBOT_ADDRESS, ROBOT_PORT) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
