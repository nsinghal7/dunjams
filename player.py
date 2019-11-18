from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock as kivyClock

import numpy as np

from entity import Entity, EntityGraphic

PLAYER_SPEED = 10


class Player(Entity):
    def __init__(self, map):
        super(Player, self).__init__()
        self.map = map
        self.position = map.player_start_location()
        self.graphic = PlayerGraphic(self.position, map)
        self.draw_graphics()

    def on_beat(self, map, music, movement):
        delta = movement.get_delta()

        # collision detection
        new_pos = (self.position[0] + delta[0], self.position[1] + delta[1])
        if self.map.is_square_passable(new_pos):
            self.position = new_pos
            self.graphic.set_position(self.position)

        map.add_player(self.position, self)

    def return_to_start(self):
        self.position = self.map.player_start_location()
        self.graphic.set_position(self.position)
        self.map.add_player(self.position, self)

class PlayerGraphic(EntityGraphic):
    def __init__(self, position, map):
        super(PlayerGraphic, self).__init__()

        self.position = np.array(position)
        self.goal_position = np.array(position)
        self.map = map

        self.color = Color(1, 1, 1)
        self.add(self.color)

        self.rect = Rectangle(pos=map.tile_to_pixels(position), size=map.tile_size())
        self.add(self.rect)

    def set_position(self, position):
        self.goal_position = np.array(position)

    def on_update(self):
        dt = kivyClock.frametime

        disp = self.goal_position - self.position
        dist = np.linalg.norm(disp)

        if dist < dt * PLAYER_SPEED:
            self.position = self.goal_position
        else:
            delta = disp * dt * PLAYER_SPEED / dist
            self.position = self.position + delta

        self.rect.pos = self.map.tile_to_pixels(self.position)
        self.rect.size = self.map.tile_size()