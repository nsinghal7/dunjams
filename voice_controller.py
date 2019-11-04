from music_controller import MusicController, PitchEvent
from input_demo import PitchDetector

class VoiceController(MusicController):
    def __init__(self):
        super(VoiceController, self).__init__()

        #self.pitch_detector = PitchDetector()

    def receive_audio(self, frames, num_channels):
        assert(num_channels == 1)

        self.music.add_event(PitchEvent(self.pitch_detector.write(frames), frames[0]))