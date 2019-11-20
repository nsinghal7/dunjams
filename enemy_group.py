import json

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from common.gfxutil import AnimGroup
from common.note import NoteGenerator, Envelope

from enemy import Enemy

def enemy_groups_from_spec(filename, map, mixer, pitch_bar):
    with open(filename) as f:
        data = json.load(f)
        return [EnemyGroup(desc, map, mixer, pitch_bar) for desc in data]

class EnemyGroup(InstructionGroup):
    def __init__(self, description, map, mixer, pitch_bar):
        super(EnemyGroup, self).__init__()
        self.mixer = mixer
        enemy_descs = description["enemies"]
        self.melody = description["melody"]
        self.type = description["pacify"] # this will be either 'individual' or 'all'
        self.melody_progress = 0 # how many correct notes in a row, used for pacifying all of them
        self.melody_index = 0 # index of next note to expect/play
        self.melody_complete = False # for 'all' type groups, keep track if the whole melody is completed

        self.cur_pitch = None


        self.enemies = AnimGroup()
        self.projectiles = AnimGroup()
        self.add(self.enemies)
        for desc in enemy_descs:
            self.enemies.add(Enemy(desc, EnemyActionDescription(desc, self), map, self.is_enemy_pacified))

        self.pitch_bar = pitch_bar

    # return a list of the IDs of pacified enemies
    def get_pacified_enemies(self):
        # if all the enemies have to be pacified at once
        if self.type == "all":
            if self.melody_complete:
                # return all the IDs if the melody has been completed
                return [e.id for e in self.enemies.objects]
            else:
                return []
        # otherwise return a list of enemies whose pacifying note is the current note
        else:
            return [e.id for e in filter(lambda e: e.note == self.cur_pitch, self.enemies.objects)]

    # a callback for enemies to see if they're pacified
    def is_enemy_pacified(self, id):
        return id in self.get_pacified_enemies()

    def on_beat_exact(self):
        # play melody exactly on the beat so it doesn't sound weird
        note = NoteGenerator(self.melody[self.melody_index], .3)
        env = Envelope(note, .02, 1, .3, 1)
        self.mixer.add(env)

        self.pitch_bar.on_enemy_note(self.melody[self.melody_index])

    def on_beat(self, map, music, movement):
        # check if player sang correct note (or if no note was required)
        # TODO: check if player doesn't sing a note when none is required
        # Increment the melody progress for all or nothing groups
        if self.melody[self.melody_index - 1] == 0 or (music.is_pitch() and
                        music.get_midi() == self.melody[self.melody_index - 1]):
            # correct pitch
            self.melody_progress += 1
        else:
            # messed up! immediately reset progress
            self.melody_progress = 0

        if self.melody_progress >= len(self.melody):
            self.melody_complete = True

        self.melody_index = (self.melody_index + 1) % len(self.melody)

        # Set the current pitch for the group
        # important for seeing if an enemy is pacified
        if music.is_pitch():
            self.cur_pitch = music.get_midi()

        # add the projectiles to the enemy group
        # for enemy in self.enemies.objects:
        #     projectile = enemy.get_projectile()
        #     if projectile != None:
        #         self.projectiles.add(projectile)

        for enemy in self.enemies.objects:
            enemy.on_beat(map, music, movement)
        # for projectile in self.projectiles.objects:
        #     projectile.on_beat(map, music, movement)

    def on_update(self, dt=None):
        self.enemies.on_update()
        self.projectiles.on_update()

class EnemyActionDescription:
    def __init__(self, description, enemy_group):
        self.motions = description["motions"]
        self.attacks = description["attacks"]
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

    def get_next_attack(self):
        attack = self.attacks[self.attack_index]
        self.attack_index = (self.attack_index + 1) % len(self.attacks)
        if self.id in self.enemy_group.get_pacified_enemies():
            return ""
        return attack
