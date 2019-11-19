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
from voice_controller import VoiceController
from keyboard_controller import KeyboardController
from player import Player
from enemy_group import EnemyGroup, enemy_groups_from_spec
from beat_bar import BeatBar
from pitch_bar import PitchBar

WORLD = "data/basic_world"
EPSILON_BEFORE_TICKS = 40
EPSILON_AFTER_TICKS = 140

MAP_WIDTH_RATIO = 1
MAP_HEIGHT_RATIO = .8

RESET_PAUSE_TIME = 2

class SplashScreen(InstructionGroup):
    def __init__(self, splash_name, mixer, sched, game):
        super(SplashScreen, self).__init__()
        self.game = game
        # TODO draw self

    def unload(self):
        # TODO: clean up anything that needs cleaning up before this splash screen can
        # be removed. This includes removing any audio or scheduler callbacks
        pass

    def on_key_down(self, keycode, modifiers):
        self.game.next_screen()

    def on_update(self):
        pass

class Level(InstructionGroup):
    def __init__(self, level_name, mixer, sched, music_controller, movement_controller, game):
        super(Level, self).__init__()
        self.game = game
        self.mixer = mixer
        self.sched = sched
        self.music_controller = music_controller
        self.movement_controller = movement_controller

        self.map = Map(WORLD + "/" + level_name + "/map.txt", MAP_WIDTH_RATIO, MAP_HEIGHT_RATIO)
        self.add(self.map)
        self.pitch_bar = PitchBar(55, MAP_WIDTH_RATIO, 1 - MAP_HEIGHT_RATIO)
        self.add(self.pitch_bar)
        #self.beat_bar = BeatBar(1, 1 - MAP_HEIGHT_RATIO)
        #self.add(self.beat_bar)

        self.music_controller.pitch_bar = self.pitch_bar

        self.restart_pause_time_remaining = 0

        self.enemy_groups = enemy_groups_from_spec(WORLD + "/" + level_name + "/enemies.json",
                                                    self.map, self.mixer, self.pitch_bar)
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
        self.map.start_new_timestep()
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

        if self.restart_pause_time_remaining > 0:
            # player can't move due to losing recently
            self.restart_pause_time_remaining -= 1
            print("got here: ", self.player.position)
        else:
            self.player.on_beat(self.map, music_input, movement)
            print("moving: ", self.player.position)

        # handle game over
        if self.map.is_square_dangerous(self.map.player_location()):
            print("restarting: ")
            self.restart()

        # handle move to next level
        if self.map.is_player_at_exit():
            self.game.next_screen()

        print("beat off")

    def restart(self):
        self.player.return_to_start()
        self.restart_pause_time_remaining = RESET_PAUSE_TIME

    def unload(self):
        self.sched.remove(self.cmd_beat_off)
        self.sched.remove(self.cmd_beat_on)
        self.sched.remove(self.cmd_beat_on_exact)

    def on_key_down(self, keycode, modifiers):
        pass

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
        self.mixer = Mixer()
        self.tempo_map = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.mixer)

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
            self.screen = SplashScreen(name, self.mixer, self.sched, self)
        elif screen_type == "level":
            self.screen = Level(name, self.mixer, self.sched, self.music_controller,
                                self.movement_controller, self)
        self.canvas.add(self.screen)

    def unload_screen(self):
        self.screen.unload()
        self.canvas.remove(self.screen)
        self.screen = None

    def next_screen(self):
        self.unload_screen()
        self.screen_index += 1
        self.load_screen()

    def on_update(self):
        self.screen.on_update()
        self.audio.on_update()

    def receive_audio(self, frames, num_channels):
        self.music_controller.receive_audio(frames, num_channels)

    def on_key_down(self, keycode, modifiers):
        self.movement_controller.on_key_down(keycode, modifiers)
        self.screen.on_key_down(keycode, modifiers)

    def on_key_up(self, keycode):
        self.movement_controller.on_key_up(keycode)

if __name__ == '__main__':
    run(Game)
