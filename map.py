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
        for row in self.tiles:
            assert(len(row) == length)
            for c in row:
                assert(c in VALID_TILES)

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

if __name__ == '__main__':
    # tests for the map class
    test = Map("data/test/map.txt")
    try:
        Map("data/test/badmap.txt")
        raise Exception("badmap didn't fail map test")
    except AssertionError:
        print("assertions succeeded")