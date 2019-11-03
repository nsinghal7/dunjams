from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate

class Entity(InstructionGroup):
    def __init__(self):
        super(Entity, self).__init__()
        pass

    def on_beat(self, map, music, movement):
        pass

    def on_update(self):
        pass