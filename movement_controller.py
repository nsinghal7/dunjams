from common.core import lookup
from time import time

class MovementController(object):
    def __init__(self):
        self.movement = (0, 0)
        self.onbeat = False

    def beat_on(self):
        self.onbeat = True

    def beat_off(self):
        self.onbeat = False

    def get_movement(self):
        return self.movement
