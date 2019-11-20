import os
os.environ['KIVY_IMAGE'] = 'sdl2'

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from kivy.clock import Clock as kivyClock

from entity import Entity, EntityGraphic
from common.gfxutil import CRectangle, AnimGroup
import numpy as np


PROJECTILE_SPEED = 10
ENEMY_SPEED = 10
# this is the amount of time during which the note bounces in sec
BOUNCE_TIME = 0.15
# maximum bounce height as a function of tile size
MAX_BOUNCE_HEIGHT = 0.5

class Enemy(Entity):
    def __init__(self, desc, action_description, map, is_enemy_pacified):
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
        # this is a callback from enemy_group, which takes in an enemy id and returns
        # whether it is pacified or not (usually just call it with your own id)
        self.is_enemy_pacified = is_enemy_pacified

        pixel_pos = self.map.tile_to_pixels(self.pos)

        self.sprites = desc["sprites"]
        if self.is_enemy_pacified(self.id):
            sprite = desc["sprites"]["pacified"]
        else:
            sprite = desc["sprites"]["angry"]
        self.graphic = EnemyGraphic(self.pos, sprite, map)
        self.draw_graphics()
        self.projectiles = AnimGroup()
        self.add(self.projectiles)

    # return the next projectile, or None if no projectile is being created
    def get_projectile(self):
        next_attack = self.actions.get_next_attack()
        if (not self.is_enemy_pacified(self.id)) and next_attack != '':
            p_pos = np.array(self.pos)
            return Projectile(p_pos, next_attack, self.map, self.sprites["projectile"])
        return None

    def on_half_beat(self, map, music):
        if self.is_enemy_pacified(self.id):
            self.projectiles.clear()

    def on_beat(self, map, music, movement):
        # move the enemy
        self.pos = self.actions.get_next_pos(self.pos)
        # self.graphic.pos = self.map.tile_to_pixels(self.pos)
        self.graphic.set_position(self.pos)

        # update the sprite to a pacified or angry one
        if self.is_enemy_pacified(self.id):
            self.graphic.set_sprite(self.sprites["pacified"])
        else:
            self.graphic.set_sprite(self.sprites["angry"])

        projectile = self.get_projectile()
        if projectile != None:
            self.projectiles.add(projectile)

        for p in self.projectiles.objects:
            p.on_beat(map, music, movement)

        # add the enemy to the map so it knows where they are
        # using its add_enemy(self, position, enemy):
        map.add_enemy(self.pos, self)

    def on_update(self, dt=None):
        self.projectiles.on_update()
        return self.graphic.on_update()


class EnemyGraphic(EntityGraphic):
    def __init__(self, init_pos, sprite, map):
        super(EnemyGraphic, self).__init__()
        self.pos = init_pos
        self.next_pos = self.pos
        self.map = map

        self.add(Color())

        if sprite:
            self.rect = Rectangle(pos=self.map.tile_to_pixels(self.pos), size=map.tile_size(), source=sprite)
        else:
            self.rect = Rectangle(pos=self.map.tile_to_pixels(self.pos), size=map.tile_size(), color=(1,0.8,0.8))
        self.add(self.rect)

    def set_position(self, new_pos):
        self.next_pos = new_pos

    def set_sprite(self, sprite):
        self.sprite = sprite
        self.rect.source = sprite

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

        return True

# map a direction character to a deltax and deltay
direction_map = {
    'u': (-1, 0),
    'd': (1, 0),
    'l': (0, -1),
    'r': (0, 1)
}


# The class that keeps track of projectiles and their positions, and moves them
class Projectile(Entity):
    def __init__(self, init_pos, dir, map, sprite):
        super(Projectile, self).__init__()
        self.pos = np.array(init_pos)
        self.next_pos = self.pos
        # the direction is "u", "d", "l", or "r"
        self.dir = dir
        self.map = map

        self.graphic = ProjectileGraphic(init_pos, map)
        # self.draw_graphics()
        # self.add(self.graphic)
        pixel_pos = self.map.tile_to_pixels(self.pos)
        self.pixel_size = np.array(map.tile_size())*0.5

        # self.add(Color(0,0.8,0.8))
        self.rect = Rectangle(pos=pixel_pos, size=map.tile_size(), source=sprite)

        # self.rect = Rectangle(pos=pixel_pos + self.pixel_size / 2, size=self.pixel_size, source=sprite)
        self.add(self.rect)

        # keep track of where we are in the bounce
        self.bouncing = False
        self.bounce_prog = 0

    # returns the next position
    def get_next_pos(self):
        return self.pos + direction_map[self.dir]

    def set_next_pos(self, next_pos):
        self.next_pos = next_pos

    # give the deltay based on the progress of the bounce
    def get_deltay_bounce(self):
        return 2 * self.bounce_prog ** 2 - 2 * self.bounce_prog

    def on_beat(self, map, music, movement):
        next_pos = self.get_next_pos()
        self.set_next_pos(next_pos)
        self.bouncing = True
        self.bounce_prog = 0
        map.add_enemy(next_pos, self)

    def on_update(self, dt=None):
        dt = kivyClock.frametime
        self.bounce_prog += dt / BOUNCE_TIME
        if self.bounce_prog > 1:
            self.bouncing = False
            deltay = 0
        else:
            deltay = self.get_deltay_bounce()

        disp = self.next_pos - self.pos
        dist = np.linalg.norm(disp)

        if dist < dt * PROJECTILE_SPEED:
            self.pos = self.next_pos
        else:
            delta = disp * dt * PROJECTILE_SPEED / dist
            self.pos = self.pos + delta

        # self.rect.pos = self.map.tile_to_pixels(self.pos) + self.pixel_size / 2
        self.rect.pos = self.map.tile_to_pixels(self.pos + [deltay, 0])

        return self.pos[0] > 0 and self.pos[1] > 0 and self.pos[1] < self.map.map_size()[1] and self.pos[0] < self.map.map_size()[0]


class ProjectileGraphic(EntityGraphic):
    def __init__(self, init_pos, map):
        super(ProjectileGraphic, self).__init__()
        self.pos = init_pos
        self.next_pos = init_pos
        self.map = map

        pixel_pos = self.map.tile_to_pixels(self.pos)
        self.pixel_size = np.array(map.tile_size())*0.5

        # self.add(Color(0,0.8,0.8))
        self.rect = Rectangle(pos=pixel_pos + self.pixel_size / 2, size=self.pixel_size)
        # self.rect = Rectangle(pos=(10, 10), size=(100, 100), source='./data/sprite/crappy_enemy.PNG')
        self.add(self.rect)

    def set_next_pos(self, next_pos):
        self.next_pos = next_pos

    def on_update(self, dt=None):
        dt = kivyClock.frametime

        disp = self.next_pos - self.pos
        dist = np.linalg.norm(disp)

        if dist < dt * PROJECTILE_SPEED:
            self.pos = self.next_pos
        else:
            delta = disp * dt * PROJECTILE_SPEED / dist
            self.pos = self.pos + delta

        self.rect.pos = self.map.tile_to_pixels(self.pos) + self.pixel_size / 2

        return self.pos[0] > 0 and self.pos[1] > 0 and self.pos[1] < self.map.map_size()[1] and self.pos[0] < self.map.map_size()[0]
        # return True
