from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix

from common.gfxutil import AnimGroup
from common.note import NoteGenerator, Envelope

from enemy import Enemy

class EnemyGroup(InstructionGroup):
    def __init__(self, description, map, mixer, pitch_bar, current_beat, is_pacified):
        super(EnemyGroup, self).__init__()
        self.mixer = mixer
        enemy_descs = description["enemies"]
        self.melody = description["melody"]
        self.type = description["pacify"] # this will be either 'individual' or 'all'
        self.melody_progress = 0 # how many correct notes in a row, used for pacifying all of them
        self.melody_index = current_beat % len(self.melody) # index of next note to expect/play
        # for 'all' type groups, keep track if the whole melody is completed
        self.melody_complete = is_pacified

        self.cur_pitch = None
        self.has_gotten_correct_pitch = False


        self.enemies = AnimGroup()
        self.projectiles = AnimGroup()
        self.add(self.enemies)
        for desc in enemy_descs:
            self.enemies.add(Enemy(desc, EnemyActionDescription(desc, self), map, self.is_enemy_pacified))

        self.pitch_bar = pitch_bar

    def is_group_pacified(self):
        return self.melody_complete

    # return a list of the IDs of pacified enemies
    def get_pacified_enemies(self):
        print("pitch:" + str(self.cur_pitch))
        print("self.melody__index: " + str(self.melody_index))
        print("self.melody" + str(self.melody))
        # if all the enemies have to be pacified at once
        if self.type == "all":
            if self.melody_complete:
                # return all the IDs if the melody has been completed
                return [e.id for e in self.enemies.objects]
            else:
                return []
        # otherwise return a list of enemies whose pacifying note is the current note
        else:
            idx = (self.melody_index - 1) % len(self.melody)
            if idx < len(self.enemies.objects):
                target = self.enemies.objects[idx]
                return [target.id] if target.note == self.cur_pitch else []
            else:
                return []

    # a callback for enemies to see if they're pacified
    def is_enemy_pacified(self, id):
        return id in self.get_pacified_enemies()

    def on_beat_exact(self):
        # play melody exactly on the beat so it doesn't sound weird
        note = NoteGenerator(self.melody[self.melody_index], .3)
        env = Envelope(note, .02, 1, .3, 1)
        self.mixer.add(env)

        self.pitch_bar.on_enemy_note(self.melody[self.melody_index])

    def on_half_beat(self, map, music):
        # check if player sang correct note (or if no note was required)
        # TODO: check if player doesn't sing a note when none is required
        # Increment the melody progress for all or nothing groups

        if self.melody[self.melody_index] == 0 or (music.is_pitch() and
                        music.get_midi() == self.melody[self.melody_index]):
            # correct pitch
            self.melody_progress += 1
            self.has_gotten_correct_pitch = True

        else:
            # messed up! immediately reset progress
            self.melody_progress = 0
            self.has_gotten_correct_pitch = False

        if self.melody_progress >= len(self.melody):
            self.melody_complete = True

        if music.is_pitch():
            self.cur_pitch = music.get_midi()
            print("pitch:" + str(self.cur_pitch))

        for enemy in self.enemies.objects:
            enemy.on_half_beat(map, music)

    def on_beat(self, map, music, movement):
        if not self.has_gotten_correct_pitch:
            if self.melody[self.melody_index] == 0 or (music != None and music.is_pitch() and
                            music.get_midi() == self.melody[self.melody_index]):
                # correct pitch
                self.melody_progress += 1

            if music != None and music.is_pitch():
                self.cur_pitch = music.get_midi()
                print("pitch:" + str(self.cur_pitch))


        self.has_gotten_correct_pitch = False

        for enemy in self.enemies.objects:
            enemy.on_beat(map, music, movement)

        self.melody_index = (self.melody_index + 1) % len(self.melody)


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
