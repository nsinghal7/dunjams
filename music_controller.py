PITCH_SUSTAIN_THRESHOLD = 5
SUSTAIN_TRAILING_BUFFER = 2

class MusicController(object):
    def __init__(self):
        self.onbeat = False
        self.pitch_bar = None

    def beat_on(self):
        self.onbeat = True

    def beat_off(self):
        self.onbeat = False

    def get_music(self):
        pass

class Music:
    def __init__(self):
        self.events = []

    def is_pitch(self):
        pass

    def finalize(self):
        pass

    def __str__(self):
        return str([str(event) for event in self.events])

class MusicEvent:
    def __init__(self, value, duration):
        self.value = value
        self.duration = duration

    def is_noisy(self):
        return self.duration < PITCH_SUSTAIN_THRESHOLD

    def __str__(self):
        return str((self.value, self.duration))

class Pitch(Music):
    def is_pitch(self):
        return True

    def add_pitch(self, midi):
        midi = int(round(midi))
        if midi != 0:
            midi = 60 + (midi % 12)

        if len(self.events):
            if midi == self.events[-1].value:
                self.events[-1].duration += 1
                if not self.events[-1].is_noisy():
                    self._merge_events()
            else:
                if self.events[-1].is_noisy():
                    self.events[-1].value = 0
                    self._merge_events()
                self.events.append(PitchEvent(midi, 1))
        else:
            self.events.append(PitchEvent(midi, 1))

        for event in self.events[::-1]:
            if not event.is_noisy():
                return event.value
        return 0

    def finalize(self):
        if not len(self.events):
            return

        self.events[-1].duration += SUSTAIN_TRAILING_BUFFER
        if self.events[-1].is_noisy():
            self.events[-1].value = 0
            self._merge_events()
            if len(self.events) >= 2 and self.events[-1].is_noisy():
                self.events[-1].value = self.events[-2].value
                self._merge_events()
        else:
            self._merge_events()
        self.events[-1].duration -= SUSTAIN_TRAILING_BUFFER

    def _merge_events(self):
        while len(self.events) >= 2 and (self.events[-2].is_noisy() or self.events[-2].value == self.events[-1].value):
            self.events[-2].value = self.events[-1].value
            self.events[-2].duration += self.events[-1].duration
            self.events.pop()

    def get_midi(self):
        for event in self.events[::-1]:
            if event.value != 0:
                return event.value
        return 0

class PitchEvent(MusicEvent):
    pass
