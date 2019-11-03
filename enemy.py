from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from entity import Entity

class Enemy(Entity):
    def __init__(self, init_pos, action_description, map):
        super(Enemy, self).__init__()
        # TODO
        # init_pos is (row, col)
        # action_description is a class with the methods
        # get_next_pos(prev_pos) which accepts and returns (row, col)
        # get_next_attack() which returns "u", "d", "l", "r", or "" for which direction to shoot
        #    or to indicate not to shoot.
        # map is a Map object that should be used to convert from tiles (row, col) to pixels (x, y)
        #   using the tile_to_pixels() function
        pass

    def on_beat(self, map, music, movement):
        pass

    def on_update(self, dt):
        pass