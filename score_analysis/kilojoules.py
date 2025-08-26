teleopSeconds = 3.5 * 60  # seconds
autonSeconds = 30 # seconds
jumpstartCooldown = 30 # seconds

kilojoulesForJumpstarting = 5 # assume we can do it instantaneously
kilojoulesForGenerating = 0.5 # per second

maxAutonJumping = autonSeconds / jumpstartCooldown * kilojoulesForJumpstarting * 2
maxAutonGenerating = autonSeconds * kilojoulesForGenerating * 2

maxTeleopJumping = teleopSeconds / jumpstartCooldown * kilojoulesForJumpstarting
maxTeleopGenerating = teleopSeconds * kilojoulesForGenerating

maxJumping = maxAutonJumping + maxTeleopJumping
maxGenerating = maxAutonGenerating + maxTeleopGenerating
maxKilojoules = maxJumping + maxGenerating

print(f"Maximum from jumpstarting: {maxJumping}")
print(f"Maximum from generating: {maxGenerating}")
print(f"Total maximum: {maxKilojoules}")