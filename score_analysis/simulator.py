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
#  - climb = 20pts
#     - mega-climb = 20 more points

"""
A robot can be described with the following parameters, for the purposes of scoring:
 - max speed across the ground
 - acceleration capacity
 - pickup speed
 - pickup reliability
 - scoring speed
 - scoring reliability
 - line-up speed (and maybe for each scoring bit? like scoring line-up speed, etc?)
 - color wheel speed
 - color wheel reliability
 - voltage speed
 - voltage reliability
 - climbing speed
 - boolean can do max climb
 - climbing reliability
 - climbing line-up speed

for building them, you get a certain number of points you can invest
reliability exponentially increases in cost, diminishing returns and all that
same for scoring and lineup speeds
climbing should cost a certain amount?
also like, jumpstart capacity (can we do all voltage ranges), etc.

TODO: values for autonomous

the robot can then be simulated by doing the following:
TODO: do autonomous
every tick, checks to see if our capacity is some % of our kilojoules.
 = if less than, keep cycling batteries
 = if more than, checks to see if we can jumpstart the grid soon (within some # seconds)
   = if we can, finishes current task then jumpstarts grid
   = if we can't, queues up a jumpstart task
checks to see if we are close to the end of the match (some # seconds)
 = if we are, checks to see if we should climb
 = if we aren't continues scoring batteries

"""


class RobotParemeters:
    pass #TODO FIXME

class Robot:
    pass #TODO FIXME

class GameState:
    AUTONOMOUS = 1
    TELEOP = 2

class Tasks:
    JUMPSTART = 1
    CHARGING_WHEEL = 2
    BATTERY = 3
    FLOODWATER = 4

TICK_RATE = 1/10 # each game tick is .1 seconds
FOUR_MINUTES = 1/TICK_RATE * 60 * 4

class GameController():
    """
    Actually runs the game. Can be run in parallel? idk.
    """

    def __init__(self):
        """
        TODO
        """
        self.game_state = GameState.AUTONOMOUS


    def run_game(self):
        game_tick = 0 # every tick is .1 seconds

        while game_tick < FOUR_MINUTES:
            # check game state
            if self.game_state is GameState.AUTONOMOUS:
                #TODO
                pass
            elif self.game_state is GameState.TELEOP:
                # decide what our current task should be
                pass #TODO

                # perform current task
                pass #TODO