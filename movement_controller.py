from common.core import lookup
from time import time

class MovementController(object):
    def __init__(self):
        self.movement = Movement()
        self.onbeat = False

    def beat_on(self):
        self.onbeat = True

    def beat_off(self):
        self.onbeat = False

    def get_movement(self):
        movement = self.movement
        self.movement = Movement()
        return movement

class Movement:
    def __init__(self, direction=None, onbeat=False):
        self.direction = direction
        self.onbeat = onbeat

    def get_delta(self):
        if self.direction == "u":
            return (-1, 0)
        elif self.direction == "d":
            return (1, 0)
        elif self.direction == "l":
            return (0, -1)
        elif self.direction == "r":
            return (0, 1)
        elif self.direction is None:
            return (0, 0)
        else:
            raise Exception("unknown direction")

    def is_on_beat(self):
    	return self.onbeat
