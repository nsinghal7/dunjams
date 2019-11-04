from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from entity import Entity, EntityGraphic
from common.gfxutil import CRectangle
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
        self.actions = action_description

        pixel_pos = self.map.tile_to_pixels(self.pos)
        self.graphic = Rectangle(pos=pixel_pos, size=map.tile_size(), color=(0,1,0))
        self.add(self.graphic)
        self.projectiles = []


    def on_beat(self, map, music, movement):
        # move the enemy
        self.pos = self.actions.get_next_pos(self.pos)
        self.graphic.pos = self.map.tile_to_pixels(self.pos)

        # make the next projectile
        next_attack = self.actions.get_next_attack()
        if next_attack != '':
            p_pos = np.array(self.pos)
            self.projectiles.append(Projectile(p_pos, next_attack, self.map))
            self.add(self.projectiles[-1])

        # TODO: get rid of projectiles that have gone off the edge of the screen

        # add them to the map so it knows where they are
        # using its add_enemy(self, position, enemy):
        map.add_enemy(self.pos, self)

        for p in self.projectiles:
            map.add_enemy(p.get_next_pos(), p)

    # use superclass's on_update
    def on_update(self, dt):
        pass


direction_map = {
    'u': (-1, 0),
    'd': (1, 0),
    'l': (0, -1),
    'r': (0, 1)
}

# The class that keeps track of projectiles and their positions, and moves them
class Projectile(Entity):
    def __init__(self, init_pos, dir, map):
        super(Projectile, self).__init__()
        self.pos = np.array(init_pos)
        # the direction is "u", "d", "l", or "r"
        self.dir = dir
        self.map = map
        pixel_pos = self.map.tile_to_pixels(self.pos)
        self.rect = Rectangle(pos=pixel_pos, size=np.array(map.tile_size())*0.5, color=(1,0.8,0.8))
        self.add(self.rect)

    def get_next_pos(self):
        self.pos += direction_map[self.dir]
        self.rect.pos = self.map.tile_to_pixels(self.pos)
        print(self.dir)
        return self.pos

    def on_update():
        pass



class EnemyGraphic(EntityGraphic):
    def __init__(self, init_pos):
        self.pos = init_pos
