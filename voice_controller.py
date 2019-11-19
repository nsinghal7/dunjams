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
        if len(self.music.events) > 3:
            self.music.events = self.music.events[-3:]
        return music

    def receive_audio(self, frames, num_channels):
        assert(num_channels == 1)

        '''
        if self.onbeat:
            return
        '''

        midi = self.pitch_detector.write(frames)
        cur = self.music.add_pitch(midi)
        if self.pitch_bar:
            self.pitch_bar.on_player_note(cur)
