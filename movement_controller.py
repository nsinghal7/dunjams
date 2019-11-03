from common.core import lookup

class MovementController:
    def __init__(self):
        self.movement = None

    def beat_on(self):
        self.movement = None

    def beat_off(self):
        pass

    def on_key_down(self, keycode, modifiers):
        if keycode[1] in ["up", "down", "right", "left"]:
            self.movement = keycode[1][0]

    def get_movement(self):
        return Movement(self.movement)

class Movement:
    def __init__(self, direction):
        self.direction = direction

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