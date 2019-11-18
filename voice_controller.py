from music_controller import MusicController, Pitch, PitchEvent
from input_demo import PitchDetector

class VoiceController(MusicController):
    def __init__(self):
        super(VoiceController, self).__init__()

        self.music = Pitch()
        self.pitch_detector = PitchDetector()

    def get_music(self):
        self.music.finalize()
        music = self.music
        self.music = Pitch()
        return music

    def receive_audio(self, frames, num_channels):
        assert(num_channels == 1)

        '''
        if self.onbeat:
            return
        '''

        self.music.add_pitch(self.pitch_detector.write(frames))
