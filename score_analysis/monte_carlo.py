from math import floor
from random import random, randint

def rand_bool():
    return True if random() > .5 else False

class Robot:
    def __init__(self, can_leave_auto, cycle_time, auto_cycle_time, can_score_high, climb_time, can_climb_high, can_jumpstart_auto, jumpstart_time, can_charge_auto, charge_time) -> None:
        # a time of -1 indicates no capability / not applicable
        self.can_leave_auto = can_leave_auto

        self.cycle_time = cycle_time
        self.auto_cycle_time = auto_cycle_time
        self.can_score_high = can_score_high

        self.climb_time = climb_time
        self.can_climb_high = can_climb_high

        self.can_jumpstart_auto = can_jumpstart_auto
        self.jumpstart_time = jumpstart_time

        self.can_charge_auto = can_charge_auto
        self.charge_time = charge_time

# point values
AUTO_LEAVE_POINTS = 3
AUTO_BATTERY_POINTS = 8
AUTO_JUMPSTART_KILOJOULES = 10
AUTO_CHARGING_KILOJOULES = 1 # per second

TELEOP_BATTERY_POINTS = 5
TELEOP_JUMPSTART_KILOJOULES = 5
TELEOP_CHARGING_KILOJOULES = .5 # per second

CLIMB_POINTS = 10
HIGH_CLIMB_POINTS = 20

AUTO_SECONDS = 30
TELEOP_SECONDS = 60 * 3.5

def calculate_score(robot: Robot) -> float:
    score = 0
    capacity = 0
    kilojoules = 0

    #TODO keep track of batteries scored and don't let us score more than 20 or something

    #TODO FIXME this doesn't take up any time???
    score += AUTO_LEAVE_POINTS if robot.can_leave_auto else 0

    if robot.auto_cycle_time > 0:
        score += floor(AUTO_BATTERY_POINTS * (AUTO_SECONDS / robot.auto_cycle_time))
        capacity += floor(1 * (AUTO_SECONDS / robot.auto_cycle_time))

    # always prioritize climbing TODO FIXME what if we don't want to
    remaining_teleop_seconds = TELEOP_SECONDS
    if robot.climb_time > 0:
        score += HIGH_CLIMB_POINTS if robot.can_climb_high else CLIMB_POINTS
        remaining_teleop_seconds -= robot.climb_time
    
    # jumpstarting
    if robot.jumpstart_time > 0:
        # figure out how many times we can jumpstart
        jumpTimes = floor(remaining_teleop_seconds / robot.jumpstart_time)
        kilojoules += jumpTimes * TELEOP_JUMPSTART_KILOJOULES
        remaining_teleop_seconds -= jumpTimes * robot.jumpstart_time

    # charging
    #TODO FIXME it's not really worth it???

    # rest go to cycling batteries
    if robot.cycle_time > 0:
        score += floor(TELEOP_BATTERY_POINTS * max((remaining_teleop_seconds / robot.cycle_time), 20 if robot.can_climb_high else 10))
        capacity += floor(max((remaining_teleop_seconds / robot.cycle_time), 20 if robot.can_climb_high else 10))

    # final charging points
    score += min(kilojoules, capacity)

    return score

#TODO should be able to readd from a file or something too

def generate_random_robots(numRobots: int) -> list[Robot]:
    robots: list[Robot] = []

    for i in range(numRobots):
        robots.append(Robot(
            rand_bool(),
            randint(-1, 30),
            randint(-1, 30),
            rand_bool(),
            randint(-1, 60),
            rand_bool(),
            rand_bool(),
            randint(-1, 10),
            rand_bool(),
            randint(-1, 10)
        ))
    
    return robots

for robot in generate_random_robots(20):
    print(calculate_score(robot))