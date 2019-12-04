import numpy as np
import json
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from common.gfxutil import AnimGroup
from common.note import NoteGenerator, Envelope

from enemy import Enemy

def enemy_groups_from_spec(filename, map, mixer, pitch_bar):
    with open(filename) as f:
        specs = json.load(f)
    return [EnemyGroup(desc, map, mixer, pitch_bar) for desc in specs]


class EnemyGroup(InstructionGroup):
    def __init__(self, description, map, mixer, pitch_bar):
        super(EnemyGroup, self).__init__()
        self.map = map
        self.mixer = mixer
        self.center = np.array(description["center"])
        self.sound_thresh = description["sound_thresh"]
        self.mel_thresh = description["mel_thresh"]
        enemy_descs = description["enemies"]
        self.melody = description["melody"]
        self.type = description["pacify"] # this will be either 'individual' or 'all'
        self.melody_progress = 0 # how many correct notes in a row, used for pacifying all of them
        self.melody_index = 0 # index of next note to expect/play
        # for 'all' type groups, keep track if the whole melody is completed
        self.melody_complete = False

        self.cur_pitch = None
        self.pitch_matched = False # True if matched the pitch this beat already

        self.enemies = AnimGroup()
        self.projectiles = AnimGroup()
        self.add(self.enemies)
        for desc in enemy_descs:
            self.enemies.add(Enemy(desc, EnemyActionDescription(desc, self), map, self.is_enemy_pacified, self.should_p_attack))

        self.pitch_bar = pitch_bar

    def player_distance(self):
        # distance along longer axis from enemy group's center to the player
        return np.max(np.abs(self.center - self.map.player_location()))

    def is_player_in_sound_threshold(self):
        return self.player_distance() <= self.sound_thresh

    def is_player_in_melody_threshold(self):
        return self.player_distance() <= self.mel_thresh

    def is_group_pacified(self):
        return self.melody_complete

    # return a list of the IDs of pacified enemies
    def get_pacified_enemies(self):
        # nobody is angry if you're outside the melody threshold
        if not self.is_player_in_melody_threshold():
            return [e.id for e in self.enemies.objects]
        if self.type == "all":
            # if all the enemies have to be pacified at once
            if self.melody_complete:
                # return all the IDs if the melody has been completed
                return [e.id for e in self.enemies.objects]
            else:
                result = []
                idx = (self.melody_index - 1 - int(not self.pitch_matched)) % len(self.melody)
                for i in range(self.melody_progress):
                    result.append(self.enemies.objects[idx - i].id)
                return result
        # otherwise return a list of enemies whose pacifying note is the current note
        else:
            idx = (self.melody_index - 1) % len(self.melody)
            if idx < len(self.enemies.objects):
                target = self.enemies.objects[idx]
                return [target.id] if 60 + target.note % 12 == self.cur_pitch else []
            else:
                return []

    # a callback for enemies to see if they're pacified
    def is_enemy_pacified(self, id):
        return id in self.get_pacified_enemies()

    def should_p_attack(self, id):
        return self.is_group_pacified() or (self.is_player_in_melody_threshold() and self.is_enemy_pacified(id))

    def on_beat_exact(self):
        if self.is_group_pacified():
            for e in self.enemies.objects:
                e.set_color(1, 1, self.pitch_bar.base_midi)
        # player is far away, enemies passive
        if not self.is_player_in_sound_threshold():
            if not self.is_group_pacified():
                for e in self.enemies.objects:
                    e.set_color(0, 0.8, self.pitch_bar.base_midi)
        else:
            self.pitch_bar.on_enemy_note(self.melody[self.melody_index])
            if self.is_group_pacified() or not self.is_player_in_melody_threshold():
                # play melody exactly on the beat so it doesn't sound weird
                note = NoteGenerator(self.melody[self.melody_index], .6, timbre="square")
                env = Envelope(note, .02, 1, .5, 1)
                self.mixer.add(env)

                if not self.is_group_pacified():
                    # player is previewing the enemies
                    for e in self.enemies.objects:
                        e.set_color(0, 0.9, self.pitch_bar.base_midi)

                    # color the correct enemy
                    idx = (self.melody_index) % len(self.melody)
                    if idx < len(self.enemies.objects):
                        target = self.enemies.objects[idx]
                        target.set_color(0.75, 0.9, self.pitch_bar.base_midi)

    def check_note(self, map, music, is_last):
        # check if player sang correct note (or if no note was required)
        # Increment the melody progress for all or nothing groups

        if not self.pitch_matched and self.is_player_in_melody_threshold():
            if self.melody[self.melody_index] == 0 or (music.is_pitch() and
                            music.to_saturation(self.melody[self.melody_index - 1]) == 1):
                # correct pitch
                self.melody_progress += 1
                self.pitch_matched = True
            elif is_last:
                # incorrect pitch for all samples, and this is the last one, so we now punish
                self.melody_progress = 0

            if self.melody_progress >= len(self.melody):
                self.melody_complete = True

            if music.is_pitch():
                self.cur_pitch = music.get_held_midi()

            for e in self.enemies.objects:
                e.set_color(0, 1, self.pitch_bar.base_midi)
            self.enemies.objects[self.melody_index - 1].set_color(music.to_saturation(self.melody[self.melody_index - 1]), 1, self.pitch_bar.base_midi)
            for eid in self.get_pacified_enemies():
                self.enemies.objects[eid].set_color(1, 1,self.pitch_bar.base_midi)
        elif not self.pitch_matched:
            self.cur_pitch = 0

        for enemy in self.enemies.objects:
            enemy.update_sprite()

    def on_beat(self, map, music, movement):
        self.check_note(map, music, True)

        for enemy in self.enemies.objects:
            enemy.on_beat(map, music, movement)

        self.pitch_matched = False

        self.melody_index = (self.melody_index + 1) % len(self.melody)


    def on_update(self, dt=None):
        self.enemies.on_update()
        self.projectiles.on_update()

class EnemyActionDescription:
    def __init__(self, description, enemy_group):
        self.motions = description["motions"]
        self.attacks = description["attacks"]
        self.p_attacks = description["p_attacks"] if "p_attacks" in description else None
        self.id = description["id"]
        self.enemy_group = enemy_group

        if len(self.motions) == 0:
            self.motions = [(0, 0)]

        if len(self.attacks) == 0:
            self.attacks = [""]

        self.motion_index = 0
        self.attack_index = 0

    def get_next_pos(self, old_pos):
        drow, dcol = self.motions[self.motion_index]
        self.motion_index = (self.motion_index + 1) % len(self.motions)
        return old_pos[0] + drow, old_pos[1] + dcol

    def get_next_attack(self, should_p_attack):
        if should_p_attack:
            attack = self.p_attacks[self.attack_index] if self.p_attacks else ""
        else:
            attack = self.attacks[self.attack_index]
        self.attack_index = (self.attack_index + 1) % len(self.attacks)
        return attack
