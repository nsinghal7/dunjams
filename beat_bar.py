from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

# TODO: make this class be the bar on the right/bottom side of the screen indicating beat matching???
# for now it's just a colored block
class BeatBar(InstructionGroup):
        def __init__(self, width_ratio, height_ratio):
            super(BeatBar, self).__init__()
            self.width_ratio = width_ratio
            self.height_ratio = height_ratio

            self.add(Color(0, 1, 1))

            self.rect = Rectangle(pos=(0, 0), size=(1, 1))
            self.on_update() # lay our rectangle
            self.add(self.rect)

        def on_update(self):
            width_ratio = self.width_ratio
            height_ratio = self.height_ratio
            self.rect.size = (Window.width * width_ratio, Window.height * height_ratio)