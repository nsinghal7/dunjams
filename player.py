from entity import Entity

class Player(Entity):
    def __init__(self, initial_position):
        super(Player, self).__init__()
        self.position = initial_position