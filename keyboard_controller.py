from movement_controller import MovementController

class KeyboardController(MovementController):
    def __init__(self):
        super(KeyboardController, self).__init__()

        self.active_keys = []
        self.new_keys = []

    def beat_on(self):
        super(KeyboardController, self).beat_on()

        self.movement = self.get_delta()

    def beat_off(self):
        super(KeyboardController, self).beat_off()

        self.new_keys = []

    def on_key_down(self, keycode, modifiers):
        if keycode[1] in ["up", "down", "right", "left"]:
            self.active_keys.append(keycode[1][0])
            self.new_keys.append(keycode[1][0])
            self.movement = self.get_delta()

    def on_key_up(self, keycode):
        if keycode[1] in ["up", "down", "right", "left"]:
            self.active_keys.remove(keycode[1][0])
            if not self.active_keys and (self.onbeat or keycode[1][0] in self.new_keys):
                return
            self.movement = self.get_delta()

    def get_delta(self):
        d = self.active_keys[-1] if self.active_keys else None

        if d == "u":
            return (-1, 0)
        elif d == "d":
            return (1, 0)
        elif d == "l":
            return (0, -1)
        elif d == "r":
            return (0, 1)
        elif d is None:
            return (0, 0)
        else:
            raise Exception("unknown direction")
