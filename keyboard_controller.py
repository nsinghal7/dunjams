from movement_controller import MovementController, Movement

class KeyboardController(MovementController):
	def __init__(self):
		super(KeyboardController, self).__init__()

	def on_key_down(self, keycode, modifiers):
		if keycode[1] in ["up", "down", "right", "left"]:
			self.movement = Movement(keycode[1][0], self.onbeat)