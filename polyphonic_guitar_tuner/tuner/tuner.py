import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy.interpolate import interp1d
from scipy.signal import periodogram, find_peaks

from enum import Enum
from itertools import pairwise
from math import log2
from queue import Queue

class TuningMode(Enum):
    MONOPHONIC = 1
    POLYPHONIC = 2

class Tuner:

    def __init__(self, queue: Queue):
        self.CHUNK_SIZE = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.BUFFER_CHUNKS = 50
        self.ZERO_PADS = 3
        self.HPS_PARTIALS = 3
        self.THRESHOLD = 10**-6

        self.in_tune_freqs = []
        self.matched_freqs = []
        self.freq_scan_windows = {}
        self.mode = TuningMode.MONOPHONIC
        self.buffer = np.zeros(self.CHUNK_SIZE)
        self.hanning_window = np.hanning(len(self.buffer))

        self.message_queue = queue
        self.go_flag = True

    def calc_cent_diff(freq1, freq2):
        return 1200.0 * log2(freq2/freq1)

    def add_cents_to_freq(freq, cents):
        return freq * 2**(cents/1200)

    def set_freqs(self, input_freqs):
        self.in_tune_freqs = input_freqs

        cent_diffs = []
        for low_freq, high_freq in pairwise(input_freqs):
            cent_diffs.append(self.calc_cent_diff(low_freq, high_freq))
        cent_diffs = cent_diffs[0] + cent_diffs + cent_diffs[-1]

        for base_freq, (low_cents, high_cents) in zip(input_freqs, pairwise(cent_diffs)):
            low_window = self.add_cents_to_freq(base_freq, low_cents)
            high_window = self.add_cents_to_freq(base_freq, high_cents)
            self.freq_scan_windows[base_freq] = (low_window, high_window)

    def tune(self):
        p = pyaudio.PyAudio()

        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)


        while stream.is_active():
            self.check_queue()
            if not self.go_flag:
                break

            binary_data = stream.read(self.CHUNK)
            self.add_to_buffer(binary_data)
            self.match_freqs()

        stream.stop_stream()
        stream.close()
        p.terminate()

    def check_queue(self):
        while self.message_queue.qsize() > 0:
            message = self.message_queue.get()
            
            match message:
                case "end":
                    self.go_flag = False
                case _:
                    print("Unrecognized message:" + message)

    def match_freqs(self):
        padded_signal = np.pad(self.buffer * self.hanning_window, (0, len(self.buffer) * 3), "constant")
        (freqs, psd) = periodogram(padded_signal, self.RATE)
        
        spectra = []
        psd_interp = interp1d(freqs, psd, kind='nearest')
        for n in range(1, self.HPS_PARTIALS + 1):
            freqs_interp = np.linspace(0, freqs[-1] * n/self.HPS_PARTIALS, num=len(freqs))
            s = psd_interp(freqs_interp)
            spectra.append(s) 

        hps = np.product(np.abs(spectra), axis=0)
        freqs_hps = np.linspace(0, freqs[-1]/self.HPS_PARTIALS, len(freqs))
        
        peak_locs = find_peaks(hps, threshold=self.THRESHOLD)
        peak_freqs = freqs_hps[peak_locs[0]]
        peak_vals = hps[peak_locs[0]]

        # TODO: match the frequencies to the relevant notes

    def add_to_buffer(self, binary_data):
        data = np.frombuffer(binary_data, datatype=np.int16)
        np.append(self.buffer, data)
        self.buffer = self.buffer[self.CHUNK_SIZE:]
