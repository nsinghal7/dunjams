from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator
from common.wavesrc import WaveBuffer, WaveFile, make_wave_buffers
from common.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock

from map import Map
from voice_controller import VoiceController
from keyboard_controller import KeyboardController
from player import Player
from enemy_group import EnemyGroup, enemy_groups_from_spec
from beat_bar import BeatBar
from pitch_bar import PitchBar
from config import EPSILON_BEFORE, EPSILON_AFTER, HALF_BEAT_TICKS

import numpy as np

WORLD = "data/basic_world"

MAP_WIDTH_RATIO = 1
MAP_HEIGHT_RATIO = .8

RESET_PAUSE_TIME = 2 # total time spent between death and moving again
RESET_MOVE_BACK_TIME = 1 # time at which the player moves back to start

SPLASH_WIDTH_TO_HEIGHT = 16/9

class SplashScreen(InstructionGroup):
    def __init__(self, splash_name, audio, game):
        super(SplashScreen, self).__init__()
        self.game = game

        potential_width = Window.height * SPLASH_WIDTH_TO_HEIGHT
        potential_height = Window.width / SPLASH_WIDTH_TO_HEIGHT

        if potential_width > Window.width:
            img_size = (Window.width, potential_height)
            img_pos = (0, (Window.height - potential_height) / 4)
        else:
            img_size = (potential_width, Window.height)
            img_pos = ((Window.width - potential_width) / 2, 0)

        print('splash screen size: ' + str(img_size))
        print('splash screen position: ' + str(img_pos))
        print('window size: ' + str(Window.size))
        self.rect = Rectangle(pos=img_pos, size=img_size)
        self.rect.source = "data/sprites/" + splash_name
        self.add(self.rect)

    def unload(self):
        # TODO: clean up anything that needs cleaning up before this splash screen can
        # be removed. This includes removing any audio or scheduler callbacks
        pass

    def on_key_down(self, keycode, modifiers):
        self.game.next_screen()

    def receive_audio(self, frames, num_channels):
        pass

    def on_update(self):
        self.rect.size = Window.size

class Level(InstructionGroup):
    def __init__(self, level_name, audio, music_controller, movement_controller, game):
        super(Level, self).__init__()
        self.game = game
        self.audio = audio
        self.mixer = Mixer()
        with open(WORLD + "/" + level_name + "/music_timing.txt") as f:
            tempo = int(f.readline().strip())
            self.bg_music_beats_per_loop = int(f.readline().strip())
        self.tempo_map = SimpleTempoMap(tempo)
        self.sched = AudioScheduler(self.tempo_map)
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)

        self.bg_music_file = WaveFile(WORLD + "/" + level_name + "/background.wav")
        self.bg_music_gen = WaveGenerator(self.bg_music_file, loop=False) # we loop explicitly
        self.mixer.add(self.bg_music_gen)
        self.cmd_bg_music_reset = self.sched.post_at_tick(self.bg_music_reset,
                            kTicksPerQuarter * self.bg_music_beats_per_loop)

        self.music_controller = music_controller
        self.movement_controller = movement_controller

        self.map = Map(WORLD + "/" + level_name + "/advanced_map.txt", MAP_WIDTH_RATIO, MAP_HEIGHT_RATIO)
        self.add(self.map)
        self.pitch_bar = PitchBar(57, MAP_WIDTH_RATIO, 1 - MAP_HEIGHT_RATIO)
        self.add(self.pitch_bar)
        #self.beat_bar = BeatBar(1, 1 - MAP_HEIGHT_RATIO)
        #self.add(self.beat_bar)

        self.music_controller.pitch_bar = self.pitch_bar

        self.restart_pause_time_remaining = 0

        self.player = Player(self.map)
        self.add(self.player)

        self.enemy_groups = enemy_groups_from_spec(WORLD + "/" + level_name + "/enemies.json",
                                                    self.map, self.mixer, self.pitch_bar)
        for eg in self.enemy_groups:
            self.add(eg)

        next_beat = 0 # we know scheduler time is 0
        next_pre_beat = next_beat - self.tempo_map.dt_to_tick(EPSILON_BEFORE)
        next_post_beat = next_beat + self.tempo_map.dt_to_tick(EPSILON_AFTER)
        next_half_beat = next_beat + HALF_BEAT_TICKS

        self.cmd_beat_on = self.sched.post_at_tick(self.beat_on, next_pre_beat)
        self.cmd_beat_on_exact = self.sched.post_at_tick(self.beat_on_exact, next_beat)
        self.cmd_beat_off = self.sched.post_at_tick(self.beat_off, next_post_beat)
        self.cmd_half_beat = self.sched.post_at_tick(self.half_beat, next_half_beat)

        self.has_performed_beat_off = False

    def bg_music_reset(self, tick, _):
        self.cmd_bg_music_reset = self.sched.post_at_tick(self.bg_music_reset,
                                    tick + kTicksPerQuarter * self.bg_music_beats_per_loop)
        self.bg_music_gen.release()
        self.bg_music_gen = WaveGenerator(self.bg_music_file, loop=False) # we loop it explicitly
        self.mixer.add(self.bg_music_gen)

    def beat_on(self, tick, _):
        self.cmd_beat_on = self.sched.post_at_tick(self.beat_on, tick + kTicksPerQuarter)
        self.map.start_new_timestep()
        self.music_controller.beat_on()
        self.movement_controller.beat_on()

        print("beat on")

    def beat_on_exact(self, tick, _):
        self.cmd_beat_on_exact = self.sched.post_at_tick(self.beat_on_exact, tick + kTicksPerQuarter)
        self.pitch_bar.on_enemy_note(0)
        for eg in self.enemy_groups:
            eg.on_beat_exact()
            eg.on_beat(self.map, self.music_controller.get_music(), None)

        self.player.on_beat_exact()

        self.has_performed_beat_off = False
        if self.movement_controller.is_ready():
            self.perform_beat_off()

        # self.player.on_beat_exact()

    def half_beat(self, tick, _):
        self.cmd_half_beat = self.sched.post_at_tick(self.half_beat, tick + kTicksPerQuarter)
        self.music_controller.beat_off()
        music_input = self.music_controller.get_music()

        #for eg in self.enemy_groups:
        #    eg.on_half_beat(self.map, music_input)

    def beat_off(self, tick, _):
        self.cmd_beat_off = self.sched.post_at_tick(self.beat_off, tick + kTicksPerQuarter)
        self.perform_beat_off()

    def perform_beat_off(self):
        if self.has_performed_beat_off:
            return # already did it this round
        self.has_performed_beat_off = True

        self.movement_controller.beat_off()
        movement = self.movement_controller.get_movement()

        if self.restart_pause_time_remaining > 0:
            # player can't move due to losing recently
            self.restart_pause_time_remaining -= 1
            if self.restart_pause_time_remaining == RESET_MOVE_BACK_TIME:
                self.player.return_to_start()
            elif self.restart_pause_time_remaining == 0:
                self.player.set_disabled(False)
        else:
            self.player.on_beat(self.map, self.music_controller.get_music(), movement)

            # handle game over
            if self.map.is_square_dangerous(self.map.player_location()):
                self.restart()

            # handle move to next level
            if self.map.is_player_at_exit():
                self.game.next_screen()

        print("beat off")

    def receive_audio(self, frames, num_channels):
        for eg in self.enemy_groups:
            eg.check_note(self.map, self.music_controller.get_music(), False)

    def restart(self):
        self.player.set_disabled(True)
        self.restart_pause_time_remaining = RESET_PAUSE_TIME

    def unload(self):
        self.sched.remove(self.cmd_beat_off)
        self.sched.remove(self.cmd_beat_on)
        self.sched.remove(self.cmd_beat_on_exact)
        self.sched.remove(self.cmd_half_beat)
        self.sched.remove(self.cmd_bg_music_reset)
        self.bg_music_gen.release()

    def on_key_down(self, keycode, modifiers):
        if self.movement_controller.is_ready():
            self.perform_beat_off()

    def on_update(self):
        self.map.on_update(kivyClock.frametime) # MUST UPDATE FIRST
        self.pitch_bar.on_update()
        #self.beat_bar.on_update()
        for eg in self.enemy_groups:
            eg.on_update(kivyClock.frametime)
        self.player.on_update()


class Game(BaseWidget):
    def __init__(self):
        super(Game, self).__init__()

        # audio setup
        self.audio = Audio(2, input_func=self.receive_audio, num_input_channels = 1)

        self.music_controller = VoiceController()
        self.movement_controller = KeyboardController()


        # load game
        with open(WORLD + "/game_info.txt") as game_info:
            self.screens = [line.strip().split(" ") for line in game_info]

        self.screen_index = 0
        self.screen = None
        self.load_screen()

    def load_screen(self):
        screen_type, name = self.screens[self.screen_index]
        if screen_type == "splash":
            self.screen = SplashScreen(name, self.audio, self)
        elif screen_type == "level":
            self.screen = Level(name, self.audio, self.music_controller,
                                self.movement_controller, self)
        self.canvas.add(self.screen)

    def unload_screen(self):
        self.screen.unload()
        self.canvas.remove(self.screen)
        self.screen = None

    def next_screen(self):
        self.unload_screen()
        self.screen_index = (self.screen_index + 1) % len(self.screens)
        self.load_screen()

    def on_update(self):
        self.screen.on_update()
        self.audio.on_update()

    def receive_audio(self, frames, num_channels):
        self.music_controller.receive_audio(frames, num_channels)
        self.screen.receive_audio(frames, num_channels)

    def on_key_down(self, keycode, modifiers):
        self.movement_controller.on_key_down(keycode, modifiers)
        self.screen.on_key_down(keycode, modifiers)

    def on_key_up(self, keycode):
        self.movement_controller.on_key_up(keycode)

if __name__ == '__main__':
    run(Game)
