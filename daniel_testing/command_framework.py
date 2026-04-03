"""
TODO FIXME: documentation and stuff. This is based on the WPILib command-based framework (the new one, not the old one)
 which I shamelessly stole here: https://github.com/danielbrownmsm/FTC-4962-2022/tree/master/commandframework

"""

import time

from typing import Callable, List, Self

class JoystickMessage:
    def __init__(self, a: bool, b: bool, x: bool, y: bool, left_bumper: bool, right_bumper: bool, left_stick: bool, right_stick: bool, xbox_button: bool, menu: bool, screenshot: bool, dpad: int, left_stick_x: float, left_stick_y: float, right_stick_x: float, right_stick_y: float, left_trigger: float, right_trigger: float) -> None:
        #TODO FIXME fix the order of this maybe?
        self.a = a
        self.b = b
        self.x = x
        self.y = y

        self.left_bumper = left_bumper
        self.right_bumper = right_bumper

        self.left_stick = left_stick
        self.right_stick = right_stick

        self.xbox_button = xbox_button
        self.menu = menu
        self.screenshot = screenshot

        self.dpad = dpad

        self.left_stick_x = left_stick_x
        self.left_stick_y = left_stick_y

        self.right_stick_x = right_stick_x
        self.right_stick_y = right_stick_y

        self.left_trigger = left_trigger
        self.right_trigger = right_trigger

#TODO FIXME is this even correct?
DEFAULT_JOYSTICK_MESSAGE = JoystickMessage(False, False, False, False, False, False, False, False, False, False, False, -1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class Joystick:
    def __init__(self):
        self.message = DEFAULT_JOYSTICK_MESSAGE

    def update(self, message: JoystickMessage) -> None:
        self.message = message


class Action:
    """
    TODO: documentation
    """
    
    def __init__(self, callback: Callable, timeout: int) -> None:
        """
        @param callback: the callback function that is called when the Action is ran
        @param timeout: the time the Action is to run, in seconds
        """
        self.callback = callback
        self.timeout = timeout # time in seconds
        
        self.timestamp = time.time()
    
    def execute(self):
        self.callback()
    
    def is_finished(self):
        return False # TODO FIXME



class Trigger:
    def __init__(self, ActionScheduler):
        self.action = None
        self.scheduler = ActionScheduler

        self.state = False
        self.previous_state = False
    
    def when_pressed(self, action: Action) -> Self:
        if not self.previous_state and self.state:
            self.scheduler.schedule(self.action)
        return self

    def when_released(self, action: Action) -> Self:
        if self.previous_state and not self.state:
            self.scheduler.schedule(self.action)
        return self

    def while_held(self, action: Action) -> Self:
        if self.previous_state and self.state:
            self.scheduler.schedule(self.action)
        return self
    
    def update(self, controller) -> None:
        self.previous_state = self.state #TODO FIXME add a debounce

        self.state = controller.get() #TODO FIXME giant switch statement?


class SequentialAction(Action):
    def __init__(self, actions: List[Action]):
        self.actions = actions
        self.index = 0
        self.timeout = -1 #TODO FIXME
    
    def is_finished(self):
        # if we are at the end of the list
        if self.index == (len(self.actions) - 1):
            return self.actions[-1].is_finished()
        return False

    
class ActionScheduler:
    """TODO: documentation"""

    # action lists
    toExecute = []
    toRemove = []

    # requirements list (can't run an Action for the claw until the 1st one finishes?)
    #TODO FIXME we will need to add a canCancel() and cancel() and isFinished() probably...
    actuators = []
    triggers = []

    def __init__(self):
        #TODO FIXME clear all lists??? check if only one instance???
        pass
    
    def addTrigger(self, trigger: Trigger):
        self.triggers.append(trigger)
    
    def schedule(self, action: Action):
        self.toExecute.append(action)
    
    def loop(self):
        #TODO FIXME

        # check all buttons
        for trigger in self.triggers:
            trigger.run()
        
        # run all actions
        for action in self.toExecute:
            action.run()
        
        # ???