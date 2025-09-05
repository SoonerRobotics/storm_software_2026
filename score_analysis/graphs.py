from math import floor
from matplotlib import colormaps
import matplotlib.pyplot as plt
import numpy as np

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
times_spent_cycling = [s for s in range(1, TELEOP_SECONDS)] # increments of 1 second
# we can filter for more realistic cycling times later
cycle_times = [t for t in range(1, TELEOP_SECONDS)]

def get_score(cycle_time, time_spent_cycling):
    battery_points = TELEOP_BATTERY_POINTS * floor(time_spent_cycling / cycle_time)
    kilojoules = floor(TELEOP_CHARGING_KILOJOULES * (TELEOP_SECONDS - time_spent_cycling)) # per second

    return battery_points + min(battery_points, kilojoules)

X, Y = np.meshgrid(cycle_times, times_spent_cycling)
SCORES = [[get_score(x, y) for x in cycle_times] for y in times_spent_cycling]

# standard matplotlib
fig, ax = plt.subplots()

# actually graph
ax.pcolormesh(SCORES, cmap=colormaps.get("viridis"))

plt.title("TeleOp Points")
plt.xlabel("Cycle Time (seconds)")
plt.ylabel("Time Spent Cycling (seconds) [as oppossed to generating]")

plt.show()