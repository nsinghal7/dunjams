from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from kivy.clock import Clock as kivyClock

from entity import Entity, EntityGraphic
from common.gfxutil import CRectangle, AnimGroup
import numpy as np


PROJECTILE_SPEED = 7
ENEMY_SPEED = 10

class Enemy(Entity):
    def __init__(self, desc, action_description, map):
        super(Enemy, self).__init__()
        # TODO
        # init_pos is (row, col)
        # action_description is a class with the methods
        # get_next_pos(prev_pos) which accepts and returns (row, col)
        # get_next_attack() which returns "u", "d", "l", "r", or "" for which direction to shoot
        #    or to indicate not to shoot.
        # map is a Map object that should be used to convert from tiles (row, col) to pixels (x, y)
        #   using the tile_to_pixels() function
        self.id = desc["id"]
        self.pos = desc["init_pos"]
        self.note = desc["note"] # the note is either the MIDI pitch which pacifies it, or -1 if the enemy group type is "all"
        self.map = map
        self.actions = action_description

        pixel_pos = self.map.tile_to_pixels(self.pos)

        # TODO: change this! self.graphic should have an on_update(), and Rectangle doesn't.
        # Because of this, self.on_update() doesn't call super's on_update()
        self.graphic = EnemyGraphic(self.pos, map)
        self.draw_graphics()
        self.projectiles = AnimGroup()


    def on_beat(self, map, music, movement):
        # move the enemy
        self.pos = self.actions.get_next_pos(self.pos)
        # self.graphic.pos = self.map.tile_to_pixels(self.pos)
        self.graphic.set_position(self.pos)

        # make the next projectile
        next_attack = self.actions.get_next_attack()
        if next_attack != '':
            p_pos = np.array(self.pos)
            self.projectiles.add(Projectile(p_pos, next_attack, self.map))
            # self.add(self.projectiles[-1])


        # add them to the map so it knows where they are
        # using its add_enemy(self, position, enemy):
        map.add_enemy(self.pos, self)

        p_kill_list = []
        print(self.projectiles.objects)
        for p in self.projectiles.objects:
            # update the position of the projectile
            next_pos = p.get_next_pos()
            # get rid of projectiles that have gone off the edge of the screen
            # print(map.map_size())
            # print(next_pos)
            # if next_pos[0] < 0 or next_pos[1] < 0 or next_pos[1] > map.map_size()[0] or next_pos[0] > map.map_size()[1]:
            #     p_kill_list.append(p)
            # # otherwise, add them
            # else:
            # The projectile should be able to remove itself at the end of its lifetime
            map.add_enemy(next_pos, p)

        # for p in p_kill_list:
            # self.projectiles.remove(p)
            # self.remove(p)

    def on_update(self, dt=None):
        # self.graphic.pos = self.map.tile_to_pixels(self.pos)
        self.graphic.on_update()
        self.projectiles.on_update()


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
        self.next_pos = self.pos
        # the direction is "u", "d", "l", or "r"
        self.dir = dir
        self.map = map
        pixel_pos = self.map.tile_to_pixels(self.pos)
        pixel_size = np.array(map.tile_size())*0.5

        self.add(Color(1,0.8,0.8))
        self.rect = Rectangle(pos=pixel_pos + pixel_size / 2, size=pixel_size, color=(1,0.8,0.8))
        self.add(self.rect)

    # updates position and returns the new one
    def get_next_pos(self):
        self.next_pos = self.pos + direction_map[self.dir]
        self.rect.pos = self.map.tile_to_pixels(self.pos) + np.array(self.map.tile_size()) / 4
        return self.next_pos

    def on_update(self, dt):
        # dt = kivyClock.frametime

        disp = self.next_pos - self.pos
        dist = np.linalg.norm(disp)

        if dist < dt * PROJECTILE_SPEED:
            self.pos = self.next_pos
        else:
            delta = disp * dt * PROJECTILE_SPEED / dist
            self.pos = self.pos + delta

        self.rect.pos = self.map.tile_to_pixels(self.pos) + np.array(self.map.tile_size()) / 4

        return self.pos[0] > 0 and self.pos[1] > 0 and self.pos[1] > self.map.map_size()[0] and self.pos[0] > self.map.map_size()[1]




class EnemyGraphic(EntityGraphic):
    def __init__(self, init_pos, map):
        self.pos = init_pos
        self.next_pos = self.pos
        self.map = map

        self.rect = Rectangle(pos=self.map.tile_to_pixels(self.pos), size=map.tile_size(), color=(1,0.8,0.8))
        self.add(self.rect)

    def set_position(self, new_pos):
        self.next_pos = new_pos

    def on_update(self, dt=None):
        dt = kivyClock.frametime

        disp = np.array(self.next_pos) - np.array(self.pos)
        dist = np.linalg.norm(disp)

        if dist < dt * ENEMY_SPEED:
            self.pos = self.next_pos
        else:
            delta = disp * dt * ENEMY_SPEED / dist
            self.pos = self.pos + delta

        self.rect.pos = self.map.tile_to_pixels(self.pos)

        # return self.pos[0] > 0 and self.pos[1] > 0 and self.pos[1] > self.map.map_size()[0] and self.pos[0] > self.map.map_size()[1]
        return True
