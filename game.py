from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers
from common.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from kivy.clock import Clock as kivyClock

from map import Map
from music_controller import MusicController
from movement_controller import MovementController
from player import Player
from enemy_group import EnemyGroup, enemy_groups_from_spec
from beat_bar import BeatBar
from pitch_bar import PitchBar

WORLD = "data/basic_world"
EPSILON_BEFORE_TICKS = 40
EPSILON_AFTER_TICKS = 100

MAP_WIDTH_RATIO = .75
MAP_HEIGHT_RATIO = .8

class Level(InstructionGroup):
    def __init__(self, level_name, mixer, sched, music_controller, movement_controller):
        super(Level, self).__init__()
        self.mixer = mixer
        self.sched = sched
        self.music_controller = music_controller
        self.movement_controller = movement_controller

        self.map = Map(WORLD + "/" + level_name + "/map.txt", MAP_WIDTH_RATIO, MAP_HEIGHT_RATIO)
        self.add(self.map)
        self.pitch_bar = PitchBar(1 - MAP_WIDTH_RATIO, MAP_HEIGHT_RATIO)
        self.add(self.pitch_bar)
        self.beat_bar = BeatBar(1, 1 - MAP_HEIGHT_RATIO)
        self.add(self.beat_bar)

        self.enemy_groups = enemy_groups_from_spec(WORLD + "/" + level_name + "/enemies.json",
                                                    self.map, self.mixer)
        for eg in self.enemy_groups:
            self.add(eg)

        self.player = Player(self.map)
        self.add(self.player)

        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, kTicksPerQuarter) + kTicksPerQuarter
        next_pre_beat = next_beat - EPSILON_BEFORE_TICKS
        next_post_beat = next_beat + EPSILON_AFTER_TICKS

        self.cmd_beat_on = self.sched.post_at_tick(self.beat_on, next_pre_beat)
        self.cmd_beat_on_exact = self.sched.post_at_tick(self.beat_on_exact, next_beat)
        self.cmd_beat_off = self.sched.post_at_tick(self.beat_off, next_post_beat)

    def beat_on(self, tick, _):
        self.cmd_beat_on = self.sched.post_at_tick(self.beat_on, tick + kTicksPerQuarter)
        self.music_controller.beat_on()
        self.movement_controller.beat_on()
        print("beat on")

    def beat_on_exact(self, tick, _):
        self.cmd_beat_on_exact = self.sched.post_at_tick(self.beat_on_exact, tick + kTicksPerQuarter)
        for eg in self.enemy_groups:
            eg.on_beat_exact()

    def beat_off(self, tick, _):
        self.cmd_beat_off = self.sched.post_at_tick(self.beat_off, tick + kTicksPerQuarter)
        self.music_controller.beat_off()
        music_input = self.music_controller.get_music()
        self.movement_controller.beat_off()
        movement = self.movement_controller.get_movement()

        for eg in self.enemy_groups:
            eg.on_beat(self.map, music_input, movement)

        self.player.on_beat(self.map, music_input, movement)

        # TODO: handle things like game over

        print("beat off")

    def on_update(self):
        self.map.on_update(kivyClock.frametime) # MUST UPDATE FIRST
        self.pitch_bar.on_update()
        self.beat_bar.on_update()
        for eg in self.enemy_groups:
            eg.on_update()
        self.player.on_update()

class Game(BaseWidget):
    def __init__(self):
        super(Game, self).__init__()

        # audio setup
        self.audio = Audio(2, input_func=self.receive_audio, num_input_channels = 1)
        self.mixer = Mixer()
        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)

        self.music_controller = MusicController()
        self.movement_controller = MovementController()


        # load game
        with open(WORLD + "/game_info.txt") as game_info:
            self.num_levels = int(game_info.readline().strip())
            self.level_names = []
            for _ in range(self.num_levels):
                self.level_names.append(game_info.readline().strip())

        self.level_index = 0
        self.level = Level(self.level_names[self.level_index], self.mixer, self.sched,
                            self.music_controller, self.movement_controller)
        self.canvas.add(self.level)

    def on_update(self):
        self.level.on_update()
        self.audio.on_update()

    def receive_audio(self, frames, num_channels):
        self.music_controller.receive_audio()

    def on_key_down(self, keycode, modifiers):
        self.movement_controller.on_key_down(keycode, modifiers)

if __name__ == '__main__':
    run(Game)