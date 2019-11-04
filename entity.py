from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate

class Entity(InstructionGroup):
    def __init__(self):
        super(Entity, self).__init__()

    def draw_graphics(self):
        self.add(self.graphic)

    def on_beat(self, map, music, movement):
        pass

    def on_update(self):
        self.graphic.on_update()

class EntityGraphic(InstructionGroup):
    def __init__(self):
        super(EntityGraphic, self).__init__()

    def on_update(self):
        pass