import json

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from common.gfxutil import AnimGroup
from common.note import NoteGenerator, Envelope

from enemy import Enemy

def enemy_groups_from_spec(filename, map, mixer):
    with open(filename) as f:
        data = json.load(f)
        return [EnemyGroup(desc, map, mixer) for desc in data]

class EnemyGroup(InstructionGroup):
    def __init__(self, description, map, mixer):
        super(EnemyGroup, self).__init__()
        self.mixer = mixer
        enemy_descs = description["enemies"]
        self.melody = description["melody"]
        self.melody_progress = 0 # how many correct notes in a row
        self.melody_index = 0 # index of next note to expect/play

        self.enemies = AnimGroup()
        self.add(self.enemies)
        for desc in enemy_descs:
            self.enemies.add(Enemy(desc["init_pos"], EnemyActionDescription(desc, self), map))

    def is_pacified(self):
        return self.melody_progress >= len(self.melody)

    def on_beat_exact(self):
        # play melody exactly on the beat so it doesn't sound weird
        note = NoteGenerator(self.melody[self.melody_index], .3)
        env = Envelope(note, .1, 1, .3, 1)
        self.mixer.add(env)

    def on_beat(self, map, music, movement):
        # check if player sang correct note (or if no note was required)
        if self.melody[self.melody_index] == 0 or (music.is_pitch() and
                        music.get_midi() == self.melody[self.melody_index]):
            # correct pitch
            self.melody_progress += 1
        else:
            # messed up! immediately reset progress
            self.melody_progress = 0
        self.melody_index = (self.melody_index + 1) % len(self.melody)

        for enemy in self.enemies.objects:
            enemy.on_beat(map, music, movement)

    def on_update(self):
        self.enemies.on_update()

class EnemyActionDescription:
    def __init__(self, description, enemy_group):
        self.motions = description["motions"]
        self.attacks = description["attacks"]
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

    def get_next_attack(self):
        attack = self.attacks[self.attack_index]
        self.attack_index = (self.attack_index + 1) % len(self.attacks)
        if self.enemy_group.is_pacified():
            return ""
        return attack