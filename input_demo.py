#####################################################################
#
# input_demo.py
#
# Copyright (c) 2017, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################

# contains example code for some simple input (microphone) processing.
# Requires aubio (pip install aubio).


import sys
sys.path.append('..')

from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.gfxutil import topleft_label, AnimGroup, CEllipse, KFAnim
from common.mixer import Mixer

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock
from random import randint
import aubio

import numpy as np

from config import SILENCE_THRESHOLD


# First-in First-out buffer used for buffering audio data
class FIFOBuffer(object):
    def __init__(self, buf_size = 4096, buf_type = np.float):
        super(FIFOBuffer, self).__init__()

        self.buf_type = buf_type
        self.buffer = np.zeros(buf_size, dtype=buf_type)
        self.write_ptr = 0

    # how much space is available for writing
    def get_write_available(self):
        return len(self.buffer) - self.write_ptr

    # how much data is available for reading
    def get_read_available(self):
        return self.write_ptr

    # write 'signal' into buffer
    def write(self, signal):
        amt = len(signal)
        L = len(self.buffer)
        assert(self.write_ptr + amt <= L)
        self.buffer[self.write_ptr:self.write_ptr+amt] = signal
        self.write_ptr += amt

    # read 'amt' values from buffer
    def read(self, amt):
        assert(amt <= self.write_ptr)
        out = self.buffer[:amt].copy()
        remaining = self.write_ptr - amt
        self.buffer[0:remaining] = self.buffer[amt:self.write_ptr]
        self.write_ptr = remaining
        return out


# keeps track of most recent N samples.
class BufferFilter(object):
    def __init__(self, size):
        super(BufferFilter, self).__init__()
        self.buf = np.zeros(size)
        self.idx = 0

    def insert(self, value):
        self.buf[self.idx] = value
        self.idx = (self.idx + 1) % len(self.buf)

    # max filter of recent values:
    def max(self):
        return np.max(self.buf)


class PitchDetector(object):
    def __init__(self):
        super(PitchDetector, self).__init__()
        # number of frames to present to the pitch detector each time
        self.buffer_size = 1024

        # set up the pitch detector
        self.pitch_o = aubio.pitch("yin", 2048, self.buffer_size, Audio.sample_rate)
        self.pitch_o.set_tolerance(.5)
        self.pitch_o.set_unit("midi")
        self.pitch_o.set_silence(SILENCE_THRESHOLD)

        # buffer allows for always delivering a fixed buffer size to the pitch detector
        self.buffer = FIFOBuffer(self.buffer_size * 8, buf_type=np.float32)

        self.cur_pitch = 0

    # Add incoming data to pitch detector. Return estimated pitch as floating point
    # midi value.
    # Returns 0 if a strong pitch is not found.
    def write(self, signal):
        conf = 0

        self.buffer.write(signal) # insert data

        # read data in the fixed chunk sizes, as many as possible.
        # keep only the highest confidence estimate of the pitches found.
        while self.buffer.get_read_available() > self.buffer_size:
            p, c = self._process_window(self.buffer.read(self.buffer_size))
            if c > conf:
                self.cur_pitch = p
        return self.cur_pitch

    # helper function for finding the pitch of the fixed buffer signal.
    def _process_window(self, signal):
        pitch = self.pitch_o(signal)[0]
        conf = self.pitch_o.get_confidence()
        return pitch, conf


# looks at incoming audio data, detects onsets, and then a little later, classifies the onset as
# "kick" or "snare"
# calls callback function with message argument that is one of "onset", "kick", "snare"
class OnsetDectior(object):
    def __init__(self, callback):
        super(OnsetDectior, self).__init__()
        self.callback = callback

        self.last_rms = 0
        self.buffer = FIFOBuffer(4096)
        self.win_size = 512 # window length for analysis
        self.min_len = 0.1  # time (in seconds) between onset detection and classification of onset

        self.cur_onset_length = 0 # counts in seconds
        self.zc = 0               # zero-cross count

        self.active = False # is an onset happening now

        self.onset_thresh = 0.01
        self.deltas_buffer = BufferFilter(100)

    def write(self, signal):
        # use FIFO Buffer to create same-sized windows for processing
        self.buffer.write(signal)
        while self.buffer.get_read_available() >= self.win_size:
            data = self.buffer.read(self.win_size)
            self._process_window(data)

    def get_max_delta(self):
        return self.deltas_buffer.max()

    # process a single window of audio, of length self.win_size
    def _process_window(self, signal):
        # only look at the difference between current RMS and last RMS
        rms = np.sqrt(np.mean(signal ** 2))
        delta = rms - self.last_rms
        self.last_rms = rms

        self.deltas_buffer.insert(delta)


        # if delta exceeds threshold and not active:
        if not self.active and delta > self.onset_thresh:
            self.callback('onset')
            self.active = True
            self.cur_onset_length = 0  # begin timing onset length
            self.zc = 0                # begin counting zero-crossings

        self.cur_onset_length += len(signal) / float(Audio.sample_rate)

        # count and accumulate zero crossings:
        zc = np.count_nonzero(signal[1:] * signal[:-1] < 0)
        self.zc += zc

        # it's classification time!
        # classify based on a threshold value of the accumulated zero-crossings.
        if self.active and self.cur_onset_length > self.min_len:
            self.active = False
            self.callback(('kick', 'snare')[self.zc > 200])


# graphical display of a meter
class MeterDisplay(InstructionGroup):
    def __init__(self, pos, height, in_range, color):
        super(MeterDisplay, self).__init__()

        self.max_height = height
        self.range = in_range

        # dynamic rectangle for level display
        self.rect = Rectangle(pos=(1,1), size=(50,self.max_height))

        self.add(PushMatrix())
        self.add(Translate(*pos))

        # border
        w = 52
        h = self.max_height+2
        self.add(Color(1,1,1))
        self.add(Line(points=(0,0, 0,h, w,h, w,0, 0,0), width=2))

        # meter
        self.add(Color(*color))
        self.add(self.rect)

        self.add(PopMatrix())

    def set(self, level):
        h = np.interp(level, self.range, (0, self.max_height))
        self.rect.size = (50, h)


# graphical display of onsets as a growing (snare) or shrinking (kick) circle
class OnsetDisplay(InstructionGroup):
    def __init__(self, pos):
        super(OnsetDisplay, self).__init__()

        self.anim = None
        self.start_sz = 100
        self.time = 0

        self.color = Color(1,1,1,1)
        self.circle = CEllipse(cpos=(0,0), csize=(self.start_sz, self.start_sz))

        self.add(PushMatrix())
        self.add(Translate(*pos))
        self.add(self.color)
        self.add(self.circle)
        self.add(PopMatrix())

    def set_type(self, t):
        if t == 'kick':
            self.anim = KFAnim((0, 1,1,1,1, self.start_sz), (0.5, 1,0,0,1, 0))
        else:
            self.anim = KFAnim((0, 1,1,1,1, self.start_sz), (0.5, 1,1,0,0, self.start_sz*2))

    def on_update(self, dt):
        if self.anim == None:
            return True

        self.time += dt
        r,g,b,a,sz = self.anim.eval(self.time)
        self.color.rgba = r,g,b,a
        self.circle.csize = sz, sz

        return self.anim.is_active(self.time)


# continuous plotting and scrolling line
class GraphDisplay(InstructionGroup):
    def __init__(self, pos, height, num_pts, in_range, color):
        super(GraphDisplay, self).__init__()

        self.num_pts = num_pts
        self.range = in_range
        self.height = height
        self.points = np.zeros(num_pts*2, dtype = np.int)
        self.points[::2] = np.arange(num_pts) * 2
        self.idx = 0
        self.mode = 'scroll'
        self.line = Line( width = 1 )
        self.add(PushMatrix())
        self.add(Translate(*pos))
        self.add(Color(*color))
        self.add(self.line)
        self.add(PopMatrix())

    def add_point(self, y):
        y = int( np.interp( y, self.range, (0, self.height) ))

        if self.mode == 'loop':
            self.points[self.idx + 1] = y
            self.idx = (self.idx + 2) % len(self.points)

        elif self.mode == 'scroll':
            self.points[3:self.num_pts*2:2] = self.points[1:self.num_pts*2-2:2]
            self.points[1] = y

        self.line.points = self.points.tolist()



class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2, input_func=self.receive_audio, num_input_channels = 1)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)
        self.onset_detector = OnsetDectior(self.on_onset)
        self.pitch = PitchDetector()

        self.info = topleft_label()
        self.add_widget(self.info)

        self.anim_group = AnimGroup()

        self.mic_meter = MeterDisplay((50, 25),  150, (-96, 0), (.1,.9,.3))
        self.mic_graph = GraphDisplay((110, 25), 150, 300, (-96, 0), (.1,.9,.3))

        self.pitch_meter = MeterDisplay((50, 200), 150, (30, 90), (.9,.1,.3))
        self.pitch_graph = GraphDisplay((110, 200), 150, 300, (30, 90), (.9,.1,.3))

        self.canvas.add(self.mic_meter)
        self.canvas.add(self.mic_graph)
        self.canvas.add(self.pitch_meter)
        self.canvas.add(self.pitch_graph)

        self.canvas.add(self.anim_group)

        self.onset_disp = None
        self.onset_x = 0
        self.cur_pitch = 0

    def on_update(self) :
        self.audio.on_update()
        self.anim_group.on_update()

        self.info.text = 'fps:%d\n' % kivyClock.get_fps()
        self.info.text += 'load:%.2f\n' % self.audio.get_cpu_load()
        self.info.text += "pitch: %.1f\n" % self.cur_pitch
        self.info.text += 'max delta: %.3f\n' % self.onset_detector.get_max_delta()
        self.info.text += 'onset delta thresh (up/down): %.3f\n' % self.onset_detector.onset_thresh

    def receive_audio(self, frames, num_channels) :
        assert(num_channels == 1)

        # Microphone volume level, take RMS, convert to dB.
        # display on meter and graph
        rms = np.sqrt(np.mean(frames ** 2))
        rms = np.clip(rms, 1e-10, 1) # don't want log(0)
        db = 20 * np.log10(rms)      # convert from amplitude to decibels
        self.mic_meter.set(db)
        self.mic_graph.add_point(db)

        # pitch detection: get pitch and display on meter and graph
        self.cur_pitch = self.pitch.write(frames)
        self.pitch_meter.set(self.cur_pitch)
        self.pitch_graph.add_point(self.cur_pitch)

        # onset detection and classification
        self.onset_detector.write(frames)


    def on_onset(self, msg):
        if msg == 'onset':
            self.onset_disp = OnsetDisplay((400 + self.onset_x, 100))
            self.onset_x = (self.onset_x + 100) % 400
            self.anim_group.add(self.onset_disp)
        elif self.onset_disp:
            self.onset_disp.set_type(msg)
            self.onset_disp = None

    def on_key_down(self, keycode, modifiers):
        t = lookup(keycode[1], ['up', 'down'], [.001, -.001])
        if t is not None:
            self.onset_detector.onset_thresh += t

if __name__ == '__main__':
    run(MainWidget)
