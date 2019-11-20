from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from kivy.core.window import Window
import numpy as np

from map_tile import MapTile, PLAYER_START

VIEW_SPEED = 8

class Map(InstructionGroup):
    def __init__(self, map_filename, width_ratio, height_ratio):
        super(Map, self).__init__()
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio

        with open(map_filename) as f:
            rows = f.read().strip().split("\n")
        for r, row in enumerate(rows):
            for c, kind in enumerate(row):
                if kind == PLAYER_START:
                    self.player_start_loc = (r, c)

        self.view_center = np.array(self.player_start_loc)
        self.view_goal = np.array(self.player_start_loc)

        self.tiles = [[MapTile(r, c, kind, self) for c, kind in enumerate(row)]
                        for r, row in enumerate(rows)]
        for row in self.tiles:
            for tile in row:
                self.add(tile)

        # initialize per-timestep variables
        self.start_new_timestep()

    def start_new_timestep(self):
        self.enemy_map = {}
        self.player_loc = None
        self.player = None

    def add_enemy(self, position, enemy):
        # TODO: maybe force projectiles to die?
        position = tuple(position)
        if position not in self.enemy_map:
            self.enemy_map[position] = []
        self.enemy_map[position].append(enemy)

    def add_player(self, position, player):
        # TODO: maybe call player callback
        self.player_loc = tuple(position)
        self.view_goal = np.array(self.player_loc)

    def is_square_passable(self, position):
        if 0 <= position[0] < len(self.tiles) and 0 <= position[1] < len(self.tiles[0]):
            return self.tiles[position[0]][position[1]].is_passable()
        else:
            print('outside of map')
            return False # outside of map isn't passable

    def is_square_dangerous(self, position):
        if position is None:
            return False
        enemies = self.enemy_map.get(tuple(position), [])
        return len(enemies) > 0

    def is_player_at_exit(self):
        if self.player_loc is None:
            return False
        return self.tiles[self.player_loc[0]][self.player_loc[1]].is_exit()

    def player_location(self):
        return self.player_loc

    def player_start_location(self):
        return self.player_start_loc

    def map_size(self):
        return len(self.tiles), len(self.tiles[0])

    def tile_size(self):
        size = np.min(Window.size) / 11
        return size, size

    def tile_to_pixels(self, position):
        row, col = position
        tile_width, tile_height = self.tile_size()
        return (Window.width * self.width_ratio / 2 + (col - self.view_center[1] - .5) * tile_width,
                Window.height * (1 - self.height_ratio / 2) - (row - self.view_center[0] + .5) * tile_height)

    def on_update(self, dt):
        disp = self.view_goal - self.view_center
        dist = np.linalg.norm(disp)
        if dist <= dt * VIEW_SPEED:
            # can move to goal this step
            self.view_center = self.view_goal
        else:
            move = disp * dt * VIEW_SPEED / dist
            self.view_center = self.view_center + move

        # update all tiles
        for row in self.tiles:
            for tile in row:
                tile.on_update()
