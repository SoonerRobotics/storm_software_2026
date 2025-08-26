#TODO: like actual math. maybe lagrange multipliers. linear algebra or something.

import kilojoules

# may as well do the rest of the max point calculations
maxBatteries = 20
pointsPerBatteryAuto = 8
pointsPerBatteryTeleop = 5
pointsForLowClimb = 10
pointsForHighClimb = 20

capacityPerBattery = 1
maxCapacity = maxBatteries * capacityPerBattery

chargePoints = min(maxCapacity, kilojoules.maxKilojoules)

maxPoints = (maxBatteries * pointsPerBatteryAuto) + pointsForHighClimb + chargePoints

print(f"Max battery points: {maxBatteries * pointsPerBatteryAuto}")
print(f"Max capacity: {maxCapacity}, max charge points: {chargePoints}")
print(f"Maximum points: {maxPoints}")