from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers
from common.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate
from kivy.clock import Clock as kivyClock

from map import Map
from music_controller import MusicController
from movement_controller import MovementController

WORLD = "data/basic_world"

class Game(BaseWidget):
    def __init__(self):
        super(Game, self).__init__()

        # audio setup
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)

        self.music_controller = None # TODO
        self.movement_controller = None # TODO


        # load game
        with open(WORLD + "/game_info.txt") as game_info:
            self.num_levels = int(game_info.readline().strip())
            self.level_names = []
            for _ in range(self.num_levels):
                self.level_names.append(game_info.readline().strip())

        self.level_index = 0
        self.load_level()

    def unload_level(self):
        # TODO: unload the level: remove all graphics and stop stuff from the previous level
        pass

    def load_level(self):
        # for now this only involves loading the map and creating the player and enemies
        # TODO load player and enemies
        self.map = Map(WORLD + "/" + self.level_names[self.level_index] + "/map.txt")
        print(self.map.player_start_location())

    def beat_on(self, tick, _):
        self.sched.post_at_tick(self.beat_on, tick + kTicksPerQuarter)
        self.music_controller.beat_on()
        self.movement_controller.beat_on()

    def beat_off(self, tick, _):
        self.sched.post_at_tick(self.beat_off, tick + kTicksPerQuarter)
        # TODO


    def on_update(self):
        self.audio.on_update()

if __name__ == '__main__':
    run(Game)