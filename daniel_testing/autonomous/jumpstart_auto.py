
from daniel_testing.command_framework import SequentialAction


class JumpstartAuto(SequentialAction):
    def __init__(self):
        super().__init__([
            DriveAction("TODO FIXME"),
            JumpstartAction("TODO FIXME")
        ])