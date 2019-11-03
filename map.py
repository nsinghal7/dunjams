EMPTY = " "
PLAYER_START = "p"
EXIT = "e"
WALL = "w"

VALID_TILES = [EMPTY, PLAYER_START, EXIT, WALL]

class Map:
    def __init__(self, map_filename):
        with open(map_filename) as f:
            self.tiles = f.read().strip().split("\n")

        # validate map
        length = len(self.tiles[0])
        for r, row in enumerate(self.tiles):
            assert(len(row) == length)
            for i, c in enumerate(row):
                assert(c in VALID_TILES)
                if c == PLAYER_START:
                    self.player_start_loc = (r, i)
        # rename PLAYER_START to EMPTY since it is no longer useful
        r, i = self.player_start_loc
        self.tiles[r] = self.tiles[r][:i] + EMPTY + self.tiles[r][i+1:]

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

    def is_square_passable(self, position):
        return self.tiles[position[0]][position[1]] != WALL

    def is_square_dangerous(self, position):
        enemies = self.enemy_map[tuple(position)]
        return enemies is not None and len(enemies) > 0

    def player_location(self):
        return self.player_loc

    def player_start_location(self):
        return self.player_start_loc

    def map_size(self):
        return len(self.tiles), len(self.tiles[0])

if __name__ == '__main__':
    # tests for the map class
    test = Map("data/test/map.txt")
    try:
        Map("data/test/badmap.txt")
        raise Exception("badmap didn't fail map test")
    except AssertionError:
        print("assertions succeeded")