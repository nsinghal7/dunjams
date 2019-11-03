#####################################################################
#
# arpeg.py
#
# Copyright (c) 2015, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################

from .clock import kTicksPerQuarter, quantize_tick_up


class Arpeggiator(object):
    def __init__(self, sched, synth, channel=0, program=(0, 40), callback = None):
        super(Arpeggiator, self).__init__()
        # output parameters
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.callback = callback

        # arpeggio parameters:
        self.length = kTicksPerQuarter / 4
        self.articulation = 0.75
        self.pitches = [60, 64, 67, 72]
        self.direction = 'up'

        # run-time variables
        self.cur_idx = 0
        self.idx_inc = 1
        self.on_cmd = None
        self.off_cmd = None
        self.playing = False

    def start(self):
        if not self.playing:
            self.playing = True

            self.synth.program(self.channel, self.program[0], self.program[1])
            now = self.sched.get_tick()
            next_tick = quantize_tick_up(now, self.length)
            self.on_cmd  = self.sched.post_at_tick(self._noteon, next_tick, None)

    def stop(self):
        if self.playing:
            self.playing = False

            self.sched.remove(self.on_cmd)
            self.sched.remove(self.off_cmd)
            if self.off_cmd:
                self.off_cmd.execute()

            # reset these so we don't have a reference to old commands.
            self.on_cmd = None
            self.off_cmd = None

    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches):
        self.pitches = pitches
        if self.cur_idx >= len(pitches):
            self.cur_idx = len(pitches) - 1

    def set_rhythm(self, length, articulation):
        self.length = length
        self.articulation = articulation

    # dir is either 'up', 'down', or 'updown'
    def set_direction(self, direction):
        assert (direction == 'up' or direction == 'down' or direction == 'updown')
        self.direction = direction
        if direction == 'up':
            self.idx_inc = 1
        elif direction == 'down':
            self.idx_inc = -1

    # find the pitch we should play based on the notes, the current note index
    # and the direction variable.
    def _get_next_pitch(self):
        pitch = self.pitches[self.cur_idx]

        notes_len = len(self.pitches)

        # flip detection if 'updown' and at endpoint
        if self.direction == 'updown':
            if self.cur_idx == 0:
                self.idx_inc = 1
            elif self.cur_idx == notes_len-1:
                self.idx_inc = -1

        # advance index
        self.cur_idx += self.idx_inc

        # keep in bounds:
        self.cur_idx = self.cur_idx % notes_len

        return pitch

    def _noteon(self, tick, ignore):
        pitch = self._get_next_pitch()

        # play note on:
        velocity = 100
        self.synth.noteon(self.channel, pitch, velocity)

        # post the note-off at the appropriate tick:
        length = self.articulation * self.length
        off_tick = tick + length
        self.off_cmd = self.sched.post_at_tick(self._noteoff, off_tick, pitch)

        # callback:
        if self.callback:
            self.callback(tick, pitch, velocity, length)

        # post next note. quantize tick to line up with grid of current note length
        next_tick = quantize_tick_up(tick, self.length)
        self.on_cmd  = self.sched.post_at_tick(self._noteon, next_tick, None)

    def _noteoff(self, tick, pitch):
        self.synth.noteoff(self.channel, pitch)
