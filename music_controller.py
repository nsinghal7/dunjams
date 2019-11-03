class MusicController:
    def __init__(self):
        pass

    def beat_on(self):
        pass

    def beat_off(self):
        pass

    def get_music(self):
        return Pitch()

class Music:
    def is_pitch(self):
        pass

class Pitch(Music):
    def is_pitch(self):
        return True

    def get_midi(self):
        return 60