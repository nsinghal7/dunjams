from music_controller import MusicController, Pitch, PitchEvent
from input_demo import PitchDetector
import copy

class VoiceController(MusicController):
    def __init__(self):
        super(VoiceController, self).__init__()

        self.music = Pitch()
        self.pitch_detector = PitchDetector()

    def get_music(self):
        #self.music.finalize()

        music = copy.copy(self.music)
        events = []
        for event in self.music.events[::-1]:
            if len(events) < 3:
                events.insert(0, event)
            if not event.is_noisy():
                break
        self.music.events = events
        return music

    # this gets called fairly often (~15 times a beat)
    def receive_audio(self, frames, num_channels):
        assert(num_channels == 1)

        midi = self.pitch_detector.write(frames)
        cur = self.music.add_pitch(midi)
        if self.pitch_bar:
            self.pitch_bar.on_player_note(midi)
