from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

EMPTY = " "
PLAYER_START = "p"
EXIT = "e"
WALL = "w"

VALID_TILES = [EMPTY, PLAYER_START, EXIT, WALL]


class MapTile(InstructionGroup):
    def __init__(self, row, col, kind, map):
        super(MapTile, self).__init__()
        if kind == PLAYER_START:
            kind = EMPTY # replace since player start doesn't matter
        self.position = (row, col)
        self.kind = kind
        self.map = map

        if kind == EMPTY:
            self.color = Color(0, 0, 1)
        elif kind == EXIT:
            self.color = Color(0, 1, 0)
        elif kind == WALL:
            self.color = Color(1, 0, 0);
        else:
            raise Exception("Cannot draw tile with name: %s" % kind)

        self.add(self.color)
        location = self.map.tile_to_pixels(self.position)
        self.rect = Rectangle(pos=location, size=self.map.tile_size())
        self.add(self.rect)

    def is_passable(self):
        return self.kind != WALL

    def is_exit(self):
        return self.kind == EXIT

    def on_update(self):
        location = self.map.tile_to_pixels(self.position)
        self.rect.pos = location
        self.rect.size = self.map.tile_size()