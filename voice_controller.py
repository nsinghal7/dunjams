class VoiceController(PitchController):
    def __init__(self):
        super(VoiceController, self).__init__()

        self.pitch = PitchDetector()

    def receive_audio(self, frames, num_channels):
        assert(num_channels == 1)

        self.cur_pitch = self.pitch.write(frames)

    def on_key_down(self, keycode, modifiers):
        key = keycode[1]
        if key == 'w':
            self.movement = Movement(0, 1, self.onbeat)
        elif key == 'a':
            self.movement = Movement(-1, 0, self.onbeat)
        elif key == 's':
            self.movement = Movement(0, -1, self.onbeat)
        elif key == 'd':
            self.movement = Movement(1, 0, self.onbeat)