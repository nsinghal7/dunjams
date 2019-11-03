from entity import Entity

class Player(Entity):
    def __init__(self, initial_position):
        super(Player, self).__init__()
        self.position = initial_position

    def on_beat(self, map, music, movement):
        delta = movement.get_delta()
        # TODO collision detection
        self.position = (self.position[0] + delta[0], self.position[1] + delta[1])
        map.add_player(self.position, self)