from enum import Enum

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

def toTicks(minutes, seconds):
    return (1/TICK_RATE) * (60*minutes + seconds)

"""A class to describe a robot
   TODO: costs so we can do genetic algorithms/linear algebra
   TODO: be able to read from a file or somethin
   TODO: invest points into cameras/construction/software quality too? that might be a little much
"""
class RobotParameters:
    def __init__(self):
        self.max_speed = 0 # maximum speed across the ground (m/s)
        self.acceleration = 0 # maximum acceleration (m/s^2)
        
        self.pickup_speed = 0 # time it takes to pick a battery up off the ground (s)
        self.pickup_reliability = 0 # reliability of pickup mechanism (percentage)
        self.scoring_speed = 0 # time it takes to score a battery (s)
        self.scoring_reliability = 0 # reliability of scoring mechanism (percentage)
        
        #TODO FIXME do we want separate line-up speeds?
        #TODO FIXME values for autonomous (reliability, speed, etc?)

        self.charging_wheel_speed = 0 # time it takes to run the charging wheel (TODO but this is literally a points-per-second task?)
        self.charging_wheel_reliability = 0 # reliability of charging wheel mechanism (%)
        self.charging_wheel_range = [] # which RPM values can it actually run at

        self.jumpstart_speed = 0 # time it takes to jumpstart the grid (s)
        self.jumpstart_reliability = 0 # reliability of jumpstart mechanism
        
        #TODO do we need a separate time parameter for how long it takes to climb to max? vs low?
        self.floodwater_speed = 0 # time it takes to climb (s)
        self.floodwater_reliability = 0 # reliability of climbing mechanism (%)
        self.can_climb_max = False # can we get >12 inches off the field floor (boolean)

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
    
    def get_task(self, game_tick, current_task: Task, score, kilojoules, capacity) -> Task:
        if self.is_climbed:
            return Task.FLOODWATER

        if self.game_state is GameState.AUTONOMOUS:
                #TODO
                pass
        elif self.game_state is GameState.TELEOP:
            # check if we're in the middle of a task
            if current_task: #TODO FIXME ???
                return

            # check time to see if we need to climb
            if game_tick > toTicks(3, 30): # thirty seconds to climb TODO FIXME pull climb time from robotparemeters
                return Task.FLOODWATER

            # otherwise, check to see if we haven't jumpstarted in a while
            if self.ticks_since_jumpstart > toTicks(0, 30): #TODO FIXME parameters?
                #TODO FIXME also check if we even need the kilojoules, and if we'd even have the time to do it
                return Task.JUMPSTART

            # otherwise, check to see if there's anything else to do
            #TODO FIXME

            # otherwise, cycle batteries
            if self.has_battery:
                return Task.SCORE_BATTERY
            else:
                return Task.PICKUP_BATTERY


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

class GameController():
    """
    Actually runs the game. Can be run in parallel? idk.
    """

    def __init__(self):
        """
        TODO
        """
        self.game_state = GameState.AUTONOMOUS

        self.tasks_completed = {
            #TODO FIXME
        }


    def run_game(self, robot: Robot):
        game_tick = 0 # every tick is .1 seconds
        game_state = GameState.AUTONOMOUS

        current_task = Task.NONE

        score = 0
        kilojoules = 0
        capacity = 0

        last_grid_charge_ticks = 0

        #TODO FIXME ??? what are we doing here???
        while game_tick < FOUR_MINUTES:
            # manage game state
            if game_tick >= THIRTY_SECONDS and self.game_state is not GameState.TELEOP:
                self.game_state = GameState.TELEOP

            #TODO FIXME
            # get task from robot
            task = robot.get_task(game_tick, current_task, score, kilojoules, capacity)

            # perform the task
            #TODO FIXME
            task_complete = False

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

            # tick the game
            game_tick += 1

        #TODO FIXME calculate end of match charge scores
        self.score += min(self.kilojoules, self.capacity)

        print(self.score)