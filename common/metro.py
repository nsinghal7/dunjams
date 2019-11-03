
#####################################################################
#
# metro.py
#
# Copyright (c) 2016, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################

from .clock import kTicksPerQuarter, quantize_tick_up

class Metronome(object):
    """Plays a steady click every beat.
    """
    def __init__(self, sched, synth, channel = 0, program=(128, 0)):
        super(Metronome, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        # run-time variables
        self.cmd = None
        self.playing = False

    def start(self):
        if self.playing:
            return

        self.playing = True

        # set up the correct sound (program: bank and preset)
        self.synth.program(self.channel, self.program[0], self.program[1])

        # find the tick of the next beat, and make it "beat aligned"
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, 480)

        # now, post the _noteon function (and remember this command)
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

    def stop(self):
        if not self.playing:
            return 
            
        self.playing = False

        # cancel anything pending in the future.
        self.sched.remove(self.cmd)

        # reset these so we don't have a reference to old commands.
        self.cmd = None

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    def _noteon(self, tick, ignore):
        # play the note right now:
        pitch = 60
        vel = 100
        self.synth.noteon(self.channel, pitch, vel)

        # post the note off for half a beat later:
        off_tick = tick + 240
        self.sched.post_at_tick(self._noteoff, off_tick, pitch)

        # schedule the next noteon for one beat later
        next_beat = tick + 480
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

    def _noteoff(self, tick, pitch):
        # just turn off the currently sounding note.
        self.synth.noteoff(self.channel, pitch)
