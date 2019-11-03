#####################################################################
#
# audio.py
#
# Copyright (c) 2015, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################

import sys
sys.path.append('.')
sys.path.append('..')

import pyaudio
import numpy as np
from common import core
import time
import os.path

class Audio(object):
    # audio configuration parameters:
    sample_rate = 44100
    buffer_size = 512
    out_dev = None
    in_dev = None

    def __init__(self, num_channels, listen_func = None, input_func = None, num_input_channels = 1):
        super(Audio, self).__init__()

        assert(num_channels == 1 or num_channels == 2)
        self.num_channels = num_channels
        self.listen_func = listen_func
        self.input_func = input_func
        self.audio = pyaudio.PyAudio()

        self.num_input_channels = num_input_channels

        # on windows, if '-asio' found in command-line-args, use ASIO drivers
        if '-asio' in sys.argv:
            Audio.out_dev, Audio.in_dev = self._find_asio_devices()

        print('using audio params:')
        print('  samplerate: {}\n  buffersize: {}\n  outputdevice: {}\n  inputdevice: {}'.format(
            Audio.sample_rate, Audio.buffer_size, Audio.out_dev, Audio.in_dev))

        # create output stream
        self.stream = self.audio.open(format = pyaudio.paFloat32,
                                      channels = num_channels,
                                      frames_per_buffer = Audio.buffer_size,
                                      rate = Audio.sample_rate,
                                      output = True,
                                      input = False,
                                      output_device_index = Audio.out_dev)

        # create input stream
        self.input_stream = None
        if input_func:
            self.input_stream = self.audio.open(format = pyaudio.paFloat32,
                                                channels = self.num_input_channels,
                                                frames_per_buffer = Audio.buffer_size,
                                                rate = Audio.sample_rate,
                                                output = False,
                                                input = True,
                                                input_device_index = Audio.in_dev)

        self.generator = None
        self.cpu_time = 0
        core.register_terminate_func(self.close)

    def close(self) :
        self.stream.stop_stream()
        self.stream.close()
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()

        self.audio.terminate()

    # set a generator. The generator must support the method
    # generate(num_frames, num_channels), 
    # which returns a numpy array of length (num_frames * num_channels)
    def set_generator(self, gen) :
        self.generator = gen

    # return cpu time calcuating audio time in milliseconds
    def get_cpu_load(self) :
        return 1000 * self.cpu_time

    # must call this every frame.
    def on_update(self):
        t_start = time.time()

        # get input audio if desired
        if self.input_stream:
            try:
                num_frames = self.input_stream.get_read_available() # number of frames to ask for
                if num_frames:
                    data_str = self.input_stream.read(num_frames, False)
                    data_np = np.fromstring(data_str, dtype=np.float32)
                    self.input_func(data_np, self.num_input_channels)
            except IOError as e:
                print('got error', e)

        # Ask the generator to generate some audio samples.
        num_frames = self.stream.get_write_available() # number of frames to supply
        if self.generator and num_frames != 0:
            (data, continue_flag) = self.generator.generate(num_frames, self.num_channels)

            # make sure we got the correct number of frames that we requested
            assert len(data) == num_frames * self.num_channels, \
                "asked for (%d * %d) frames but got %d" % (num_frames, self.num_channels, len(data))

            # convert type if needed and write to stream
            if data.dtype != np.float32:
                data = data.astype(np.float32)
            self.stream.write(data.tostring())

            # send data to listener as well
            if self.listen_func:
                self.listen_func(data, self.num_channels)

            # continue flag
            if not continue_flag:
                self.generator = None

        # how long this all took
        dt = time.time() - t_start
        a = 0.9
        self.cpu_time = a * self.cpu_time + (1-a) * dt

    # look for the ASIO devices and return them (output, input)
    def _find_asio_devices(self):
        out_dev = in_dev = None

        cnt = self.audio.get_host_api_count()
        for i in range(cnt):
            api = self.audio.get_host_api_info_by_index(i)
            if api['type'] == pyaudio.paASIO:
                out_dev = api['defaultOutputDevice']
                in_dev = api['defaultInputDevice']
                print('Found ASIO device at index', i)

        return out_dev, in_dev



def get_audio_devices():
    '''Returns the available input and output devices as { 'input': <list>, 'output': <list> }
<list> is a list of device descriptors, each being a dictionary:
    {'index': <integer>, 'name': <string>, 'latency': (low, high), 'channels': <max # of channels>
'''

    def add_device(arr, io_type, dev) :
        info = {}
        info['index'] = dev['index']
        info['name'] = dev['name']
        info['latency'] = (dev['defaultLow' + io_type + 'Latency'], 
                           dev['defaultHigh' + io_type + 'Latency'])
        info['channels'] = dev['max' + io_type + 'Channels']
        arr.append(info)

    audio = pyaudio.PyAudio()

    out_devs = [{'index':'None', 'name':'Default', 'channels':0, 'latency':(0,0)}]
    in_devs  = [{'index':'None', 'name':'Default', 'channels':0, 'latency':(0,0)}]

    cnt = audio.get_device_count()
    for i in range(cnt):
        dev = audio.get_device_info_by_index(i)

        if dev['maxOutputChannels'] > 0:
            add_device(out_devs, 'Output', dev)

        if dev['maxInputChannels'] > 0:
            add_device(in_devs, 'Input', dev)

    audio.terminate()
    return {'output': out_devs, 'input': in_devs}


def print_audio_devices():
    devs = get_audio_devices()

    print("\nOutput Devices")
    print('{:>5}: {:<40} {:<6} {}'.format('idx', 'name', 'chans', 'latency'))
    for d in devs['output']:
        print('{index:>5}: {name:<40} {channels:<6} {latency[0]:.3f} - {latency[1]:.3f}'.format(**d))

    print("\nInput Devices")
    print('{:>5}: {:<40} {:<6} {}'.format('idx', 'name', 'chans', 'latency'))
    for d in devs['input']:
        print('{index:>5}: {name:<40} {channels:<6} {latency[0]:.3f} - {latency[1]:.3f}'.format(**d))


if __name__ == "__main__":
    print_audio_devices()
