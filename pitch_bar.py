from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

# TODO: make this class be the bar on the right/bottom side of the screen indicating pitch matching???
# for now it's just a colored block
class PitchBar(InstructionGroup):
        def __init__(self, width_ratio, height_ratio):
            super(PitchBar, self).__init__()
            self.width_ratio = width_ratio
            self.height_ratio = height_ratio

            self.add(Color(1, 1, 0))

            self.rect = Rectangle(pos=(0, 0), size=(1, 1))
            self.on_update() # lay our rectangle
            self.add(self.rect)

        def on_update(self):
            width_ratio = self.width_ratio
            height_ratio = self.height_ratio
            self.rect.pos = (Window.width * (1 - width_ratio), Window.height * (1 - height_ratio))
            self.rect.size = (Window.width * width_ratio, Window.height * height_ratio)