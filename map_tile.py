from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from random import randint

EMPTY = " "
PLAYER_START = "p"
EXIT = "e"
WALL = "w"

VALID_TILES = [EMPTY, PLAYER_START, EXIT, WALL]

SPRITE_MAP = {
    WALL: 'br_wall',
    EMPTY: 'sq_fl',
    EXIT: 'ladder.png'
}

SPRITE_PREFIX = './data/sprites/'

class MapTile(InstructionGroup):
    def __init__(self, row, col, kind, map):
        super(MapTile, self).__init__()
        if kind == PLAYER_START:
            kind = EMPTY # replace since player start doesn't matter
        self.position = (row, col)
        self.kind = kind
        self.map = map
        self.sprite = None

        location = self.map.tile_to_pixels(self.position)

        if kind == EMPTY:
            self.color = Color(0.5, 0.5, 0.5)
            self.add(self.color)
            self.sprite = SPRITE_PREFIX + SPRITE_MAP[kind] + str(randint(1, 4)) + '.png'

        elif kind == EXIT:
            self.add(Rectangle(pos=location, size=self.map.tile_size(), color=(0,0,0)))
            self.add(Color(1,1,1))
            self.sprite = SPRITE_PREFIX + SPRITE_MAP[kind]

        elif kind == WALL:
            self.add(Color(0.4, 0.4, 0.4))
            # self.sprite = SPRITE_PREFIX + SPRITE_MAP[kind]

            self.sprite = SPRITE_PREFIX + SPRITE_MAP[kind] + str(randint(1, 4)) + '.png'
        else:
            raise Exception("Cannot draw tile with name: %s" % kind)

        self.rect = Rectangle(pos=location, size=self.map.tile_size())
        if self.sprite:
            self.rect.source = self.sprite
        self.add(self.rect)

    def is_passable(self):
        return self.kind != WALL

    def is_exit(self):
        return self.kind == EXIT

    def on_update(self):
        location = self.map.tile_to_pixels(self.position)
        self.rect.pos = location
        self.rect.size = self.map.tile_size()
