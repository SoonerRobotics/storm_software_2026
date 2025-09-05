from math import floor
import matplotlib

# point values - we should really move these to a constants file, or a .CSV or .cfg or something
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
TELEOP_SECONDS = int(60 * 3.5)

# ignoring jumpstart and climb, divvy up time between generating electricity and scoring batteries
# also ignoring auton
time_spent_cycling = [s for s in range(1, TELEOP_SECONDS)] # increments of 1 second
# we can filter for more realistic cycling times later
cycle_times = [t for t in range(1, TELEOP_SECONDS)]

# time to actually calculate points, but we have two independent variables, so need a matrix
points = []
for idx, time in enumerate(time_spent_cycling):
    points.append([]) # add a new row
    
    for cycle_time in cycle_times:
        battery_points = TELEOP_BATTERY_POINTS * floor(time / cycle_time)
        kilojoules = floor(TELEOP_CHARGING_KILOJOULES * (TELEOP_SECONDS - time)) # per second

        score = battery_points + min(battery_points, kilojoules)

        points[idx].append(score)

print(points)