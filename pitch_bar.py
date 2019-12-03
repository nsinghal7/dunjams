from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.core.window import Window

import numpy

class PitchBar(InstructionGroup):
        def __init__(self, base_midi, width_ratio, height_ratio):
            super(PitchBar, self).__init__()

            self.base_midi = base_midi
            print(base_midi)
            self.width_ratio = width_ratio
            self.height_ratio = height_ratio * 0.7

            self.keys = []
            self.key_colors = []

            for i in range(12):
                color = Color(1, 1, 1)
                self.key_colors.append(color)
                self.add(color)
                key = Rectangle()
                self.keys.append(key)
                self.add(key)

            self.div_lines = []

            self.add(Color(0, 0, 0))

            for i in range(13):
                line = Line(width=3.0)
                self.div_lines.append(line)
                self.add(line)

            self.ptr_color = Color(1, 1, 1)
            self.add(self.ptr_color)
            self.ptr = Triangle()
            self.add(self.ptr)

            self.player_pitch = None
            self.enemy_pitch = None

            # keep a history of what the player has sung, max 10 pitches
            self.player_pitch_history = numpy.zeros(10)
            self.player_pitch_idx = 0
            # try to get rid of bumps
            self.smooth_pitch = 0

            self.create_keys()
            self.on_update()

        def create_keys(self):
            width_ratio = self.width_ratio
            height_ratio = self.height_ratio

            for i, key in enumerate(self.keys):
                x = Window.width * width_ratio * (i + 1) // 14
                key.pos = (x, 10)
                key.size = (Window.width * width_ratio // 14, Window.height * height_ratio)

            for i, line in enumerate(self.div_lines):
                x = Window.width * width_ratio * (i + 1) // 14
                line.points = (x, 0, x, Window.height * height_ratio + 8)

        def on_enemy_note(self, midi):
            self.set_key_color(self.enemy_pitch, (1, 1, 1))
            self.enemy_pitch = self.get_index(midi)
            self.set_key_color(self.enemy_pitch)


        # midi is given as a floating-point number
        # set player_pitch to the floating point fraction across the screen
        def on_player_note(self, midi):
            # self.set_key_color(self.player_pitch, (1, 1, 1))
            # self.player_pitch = self.get_index(midi)
            # self.set_key_color(self.player_pitch)
            if midi == 0:
                self.player_pitch = None
            else:
                self.player_pitch = (midi - self.base_midi) % 12
                self.player_pitch_history = numpy.append(self.player_pitch_history, self.player_pitch)
                self.player_pitch_history = self.player_pitch_history[1:]

            # self.smooth_pitch = self.player_pitch_history
            self.smooth_pitch = smooth(self.player_pitch_history, window_len=self.player_pitch_history.shape[0], window="blackman")


        def set_key_color(self, index, rgb=None):
            if index is not None:
                if rgb is None:
                    rgb = Color(index / 12, 1, 1, mode='hsv').rgba
                self.key_colors[index].rgb = rgb

        def get_index(self, midi):
            midi = int(round(midi))
            return None if midi == 0 else (midi - self.base_midi) % 12

        def on_update(self):
            width_ratio = self.width_ratio
            height_ratio = self.height_ratio

            self.create_keys()
            if self.player_pitch is None:
                self.ptr.points = (-1, -1, -1, -1, -1, -1)
            else:
                # set the player pointer color to that of the enemy note ONLY IF it's right
                if int(round(self.player_pitch)) == self.enemy_pitch:
                    self.ptr_color.rgb = self.key_colors[self.enemy_pitch].rgb
                else:
                    self.ptr_color.rgb = (1,1,1)

                x = Window.width * width_ratio * (self.smooth_pitch[-1] + 1) // 14 + Window.width * width_ratio // (14 * 2)
                dx = Window.width * width_ratio // (14 * 8)
                y = Window.height * height_ratio * 5 // 4 / 0.7
                dy = Window.height * height_ratio // 5 / 0.49
                self.ptr.points = (x - dx, y, x + dx, y, x, y - dy)



# a function to smooth the voice input
def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=numpy.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=numpy.ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='valid')
    return y
