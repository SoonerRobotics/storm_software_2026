from enum import Enum
from random import random, randint

# TODO: monte-carlo simulation, maybe a genetic algorithm or something, idk

# potential ways to score (matches are 4 minutes total, auton is 30s):
# auton: 
#  - batteries 8 pts each + 1 capacity
#  - kilojoules earned are doubled
#  - leave team zone for 3 pts
# teleop:
#  - batteries 5 pts each + 1 capacity
#  - charging wheel = 1 kilojoule / 2 seconds
#  - jumpstart grid (evyr 30s) 5 kilojoules
#  - climb = 10ts
#     - mega-climb = 10 more points

"""
for building them, you get a certain number of points you can invest
reliability exponentially increases in cost, diminishing returns and all that
same for scoring and lineup speeds
climbing should cost a certain amount?
also like, jumpstart capacity (can we do all voltage ranges), etc.
"""

class GameState(Enum):
    DISABLED = 0
    AUTONOMOUS = 1
    TELEOP = 2

class Task(Enum):
    NOTHING = 0

    LINEUP_PICKUP_BATTERY = 1
    PICKUP_BATTERY = 2

    LINEUP_SCORE_BATTERY = 3
    SCORE_BATTERY = 4

    LINEUP_CHARGING_WHEEL = 5
    CHARGING_WHEEL = 6

    LINEUP_JUMPSTART = 7
    JUMPSTART = 8

    LINEUP_FLOODWATER = 9
    FLOODWATER = 10

TICK_RATE = 1/10 # each game tick is .1 seconds
FOUR_MINUTES = 1/TICK_RATE * 60 * 4
THIRTY_SECONDS = 1/TICK_RATE * 30

def toTicks(minutes, seconds):
    return (1/TICK_RATE) * (60*minutes + seconds)

"""A class to describe a robot
   TODO: costs so we can do genetic algorithms/linear algebra
   TODO: be able to read from a file or somethin
   TODO: invest points into cameras/construction/software quality too? that might be a little much
"""
class RobotParameters:
    def __init__(self, max_speed, acceleration, pickup_speed, pickup_reliability, scoring_speed, scoring_reliability, charging_wheel_speed, charging_wheel_reliability, 
                 charging_wheel_range, jumpstart_speed, jumpstart_reliability, jumpstart_range, floodwater_speed, floodwater_reliability, can_climb_max):
        self.max_speed = max_speed # maximum speed across the ground (m/s)
        self.acceleration = acceleration # maximum acceleration (m/s^2)
        
        self.pickup_speed = pickup_speed # time it takes to pick a battery up off the ground (s)
        self.pickup_reliability = pickup_reliability # reliability of pickup mechanism (percentage)
        self.scoring_speed = scoring_speed # time it takes to score a battery (s)
        self.scoring_reliability = scoring_reliability # reliability of scoring mechanism (percentage)
        
        #TODO FIXME do we want separate line-up speeds?
        #TODO FIXME values for autonomous (reliability, speed, etc?)

        self.charging_wheel_speed = charging_wheel_speed # time it takes to run the charging wheel (TODO but this is literally a points-per-second task?)
        self.charging_wheel_reliability = charging_wheel_reliability # reliability of charging wheel mechanism (%)
        self.charging_wheel_range = charging_wheel_range # which RPM values can it actually run at

        self.jumpstart_speed = jumpstart_speed # time it takes to jumpstart the grid (s)
        self.jumpstart_reliability = jumpstart_reliability # reliability of jumpstart mechanism
        self.jumpstart_range = jumpstart_range # which voltage values it can actually run at
        
        #TODO do we need a separate time parameter for how long it takes to climb to max? vs low?
        self.floodwater_speed = floodwater_speed # time it takes to climb (s)
        self.floodwater_reliability = floodwater_reliability # reliability of climbing mechanism (%)
        self.can_climb_max = can_climb_max # can we get >12 inches off the field floor (boolean)

"""A class to actually hold an agent"""
class Robot:
    def __init__(self, parameters: RobotParameters):
        self.parameters = parameters

        # task states
        self.current_task = None
        self.last_task = None
        self.ticks_since_task = 0

        # robot state
        self.has_battery = True # start with one preloaded
        self.is_climbed = False # once we've climbed we can't do anything else
        self.is_lined_up = False # are we lined up with whatever we were lining up to do

        self.last_jumpstart_tick = -999
    
    def get_task(self, game_tick, current_task: Task, game_state: GameState, kilojoules, capacity) -> Task:
        #TODO FIXME should we even keep track of this? i.e. does this need to be a class variable?
        # update state stuff
        self.current_task = current_task

        if current_task is Task.JUMPSTART:
            self.last_jumpstart_tick = game_tick
        
        #TODO FIXME we shouldn't always finish the task we were previously on
        if current_task is not Task.NOTHING:
            return current_task

        if self.is_climbed:
            return Task.FLOODWATER

        if game_state is GameState.AUTONOMOUS:
                #TODO FIXME do autonomous stuff
                pass
        
        elif game_state is GameState.TELEOP:
            # check time to see if we need to climb
            if game_tick > toTicks(3, 30): # thirty seconds to climb TODO FIXME pull climb time from robotparemeters
                return Task.FLOODWATER if self.is_lined_up else Task.LINEUP_FLOODWATER

            # otherwise, check to see if we haven't jumpstarted in a while
            if (game_tick - self.last_jumpstart_tick) > toTicks(0, 30): #TODO FIXME parameters?
                #TODO FIXME also check if we even need the kilojoules, and if we'd even have the time to do it
                return Task.JUMPSTART if self.is_lined_up else Task.LINEUP_JUMPSTART

            # otherwise, cycle batteries
            if self.has_battery:
                return Task.SCORE_BATTERY if self.is_lined_up else Task.LINEUP_SCORE_BATTERY
            else:
                return Task.PICKUP_BATTERY if self.is_lined_up else Task.LINEUP_PICKUP_BATTERY
            
            #TODO FIXME this AI never runs the generator
        
        # fallback
        return Task.NOTHING

class GameController():
    """
    Actually runs the game. Can be run in parallel? idk.
    """

    def __init__(self):
        pass

    def run_game(self, robot: Robot):
        game_tick = 0 # every tick is .1 seconds
        game_state = GameState.AUTONOMOUS

        current_task = Task.NOTHING
        task_complete = False
        task_succeed = False

        score = 0
        kilojoules = 0
        capacity = 0

        last_grid_charge_ticks = 0
        ticks_at_task_start = 0

        while game_tick < FOUR_MINUTES:
            # manage game state
            if game_tick >= THIRTY_SECONDS and game_state is not GameState.TELEOP:
                self.game_state = GameState.TELEOP

            # get task from robot
            task = robot.get_task(game_tick, current_task, game_state, kilojoules, capacity)

            # reset counter if it's a new one
            if task is not current_task:
                ticks_at_task_start = game_tick
                task_complete = False

            # perform the task
            #TODO FIXME this doesn't account for robot's max_speed or acceleration
            match task:
                #TODO FIXME can we break this logic out into a function or something? this is a lot of copy and paste repeat code, not very DRY
                #TODO FIXME we're also going to have to check if they're lined up before checking if they pass the score check
                case Task.LINEUP_PICKUP_BATTERY:
                    if (game_tick - ticks_at_task_start) >= toTicks(0, robot.parameters.pickup_speed):
                        task_complete = True
                        robot.is_lined_up = True #TODO FIXME do we want separate booleans for if it's lined up for different tasks?
                case Task.PICKUP_BATTERY:
                    if robot.is_lined_up:
                        task_complete = True

                        #TODO FIXME figure out a better way to do this skill check
                        task_succeed = random() > robot.parameters.pickup_reliability

                case Task.LINEUP_SCORE_BATTERY:
                    if (game_tick - ticks_at_task_start) >= toTicks(0, robot.parameters.scoring_speed):
                        task_complete = True
                        robot.is_lined_up = True
                case Task.SCORE_BATTERY:
                    if robot.is_lined_up:
                        task_complete = True
                        task_succeed = random() > robot.parameters.scoring_reliability

                #TODO FIXME this doesn't account for the CHARGING_RANGE of the robot
                case Task.LINEUP_CHARGING_WHEEL:
                    if (game_tick - ticks_at_task_start) >= toTicks(0, robot.parameters.charging_wheel_speed):
                        task_complete = True
                        robot.is_lined_up = True
                case Task.CHARGING_WHEEL:
                    if robot.is_lined_up:
                        task_complete = True
                        task_succeed = random() > robot.parameters.charging_wheel_reliability

                #TODO FIXME this doesn't account for the JUMPSTART_RANGE of the robot
                case Task.LINEUP_JUMPSTART:
                    if (game_tick - ticks_at_task_start) >= toTicks(0, robot.parameters.jumpstart_speed):
                        task_complete = True
                        robot.is_lined_up = True
                case Task.JUMPSTART:
                    if robot.is_lined_up:
                        task_complete = True
                        task_succeed = random() > robot.parameters.jumpstart_reliability

                case Task.LINEUP_FLOODWATER:
                    if (game_tick - ticks_at_task_start) >= toTicks(0, robot.parameters.floodwater_speed):
                        task_complete = True
                        robot.is_lined_up = True
                case Task.FLOODWATER:
                    if robot.is_lined_up:
                        task_complete = True
                        task_succeed = random() > robot.parameters.floodwater_reliability

            # score the task
            if task_complete:
                match task:
                    case Task.SCORE_BATTERY:
                        score += 5 if self.game_state is GameState.TELEOP else 8
                        capacity += 1
                    case Task.CHARGING_WHEEL:
                        # also TODO FIXME this doesn't double kilos in auto rn
                        kilojoules += 2 #TODO FIXME this is like a points/second thing, that isn't reflected well here
                    case Task.JUMPSTART:
                        #TODO task validation to make sure this is legal???
                        kilojoules += 5 if self.game_state is GameState.TELEOP else 10
                        last_grid_charge_ticks = game_tick
                    case Task.FLOODWATER:
                        score += 10 #TODO how are we going to differentiate the high climb? check RobotParameters?
                
                # and reset
                current_task = Task.NOTHING
                robot.is_lined_up = False
                task_complete = False

            # tick the game
            game_tick += 1

        #TODO FIXME calculate end of match charge scores
        score += min(kilojoules, capacity)

        print(score)

def main():
    game = GameController()

    custom_params = RobotParameters(
        10.0, 10.0,
        5.0, .75,
        5.0, .80,
        3.0, .95, [],
        5.0, .85, [],
        12.0, .75, True
    )
    robot = Robot(custom_params)

    game.run_game(robot)


if __name__ == "__main__":
    main()