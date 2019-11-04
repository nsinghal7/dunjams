from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from entity import Entity, EntityGraphic
import numpy as np

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
        self.pos = init_pos
        self.map = map
        self.get_next_pos = action_description.get_next_pos
        self.get_next_attack = action_description.get_next_attack

        self.graphic = EnemyGraphic()
        self.projectiles = []


    def on_beat(self, map, music, movement):
        # move the enemy
        self.pos = self.get_next_pos(self.pos)

        # make the next projectile
        next_attack = self.get_next_attack()
        if next_attack != '':
            p_pos = np.array(self.pos) + direction_map[next_attack]
            self.projectiles.append(Projectile(p_pos, next_attack))

        # TODO: get rid of projectiles that have gone off the edge of the screen

        # add them to the map so it knows where they are
        # using its add_enemy(self, position, enemy):
        map.add_enemy(self.pos, self)

        for p in self.projectiles:
            map.add_enemy()

    # use superclass's on_update
    # def on_update(self, dt):
        # pass


direction_map = {
    'u': (0, 1),
    'd': (0, -1),
    'l': (-1, 0),
    'r': (1, 0)
}

# The class that keeps track of projectiles and their positions, and moves them
class Projectile:
    def __init__(self, init_pos, dir):
        super(Projectile, self).__init__()
        self.pos = np.array(init_pos)
        # the direction is "u", "d", "l", or "r"
        self.dir = dir

    def get_next_pos(self):
        self.pos += direction_map[self.dir]
        return self.pos


class EnemyGraphic(EntityGraphic):
    def __init__(self):
        pass
