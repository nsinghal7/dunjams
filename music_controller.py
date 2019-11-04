PITCH_SUSTAIN_THRESHOLD = 5

class MusicController(object):
    def __init__(self):
        self.music = Music()
        self.onbeat = False

    def beat_on(self):
        self.onbeat = True

    def beat_off(self):
        self.onbeat = False

    def get_music(self):
        music = self.music
        self.music = Music()
        return music

class Music:
    def __init__(self):
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def is_pitch(self):
        pass

class MusicEvent:
    def __init__(self, beat, value):
        self.beat = beat
        self.value = value

class Pitch(Music):
    def is_pitch(self):
        return True

    def add_pitch(self, t, midi):
        if len(self.events):
            if midi == self.events[-1].value:
                return
            if t - self.events[-1].beat < PITCH_SUSTAIN_THRESHOLD:
                self.events.pop()
        self.add_event(PitchEvent(t, midi))

class PitchEvent(MusicEvent):
    pass
