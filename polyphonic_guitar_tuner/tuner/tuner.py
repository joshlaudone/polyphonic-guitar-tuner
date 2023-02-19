import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy.interpolate import interp1d
from scipy.signal import periodogram, find_peaks

import time
from enum import Enum
from itertools import pairwise
from queue import Queue

from messaging.MessagesToTuner import MessageToTuner, MessageToTunerType
from messaging.MessagesToGUI import MessageToGUI, MessageToGUIType

class TuningMode(Enum):
    MONOPHONIC = 1
    POLYPHONIC = 2

class Tuner:


    @staticmethod
    def calc_cent_diff(freq1, freq2):
        return 1200.0 * np.log2(freq2/freq1)

    @staticmethod
    def add_cents_to_freq(freq, cents):
        return freq * 2**(cents/1200)

    def __init__(self, inbound_queue: Queue, outbound_queue: Queue):
        self.CHUNK_SIZE = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.BUFFER_CHUNKS = 50
        self.ZERO_PADS = 3
        self.HPS_PARTIALS = 3
        self.HPS_THRESHOLD = 10**-4

        self.in_tune_freqs = []
        self.matched_freqs = []
        self.freq_scan_windows = []
        self.middle_c_freq = 261.625565
        self.mode = TuningMode.POLYPHONIC
        self.buffer = np.zeros(self.CHUNK_SIZE * self.BUFFER_CHUNKS)
        self.hanning_window = np.hanning(len(self.buffer))

        self.inbound_queue = inbound_queue
        self.outbound_queue = outbound_queue

        self.quit_flag = False
        self.pause_flag = True

    def set_freqs(self, input_notes):
        self.in_tune_freqs = []
        self.freq_scan_windows = []
        for note_number in input_notes:
            self.in_tune_freqs.append(Tuner.add_cents_to_freq(self.middle_c_freq, note_number*100))

        cent_diffs = []
        for low_freq, high_freq in pairwise(self.in_tune_freqs):
            cent_diffs.append(Tuner.calc_cent_diff(low_freq, high_freq) / 2)
        cent_diffs = [cent_diffs[0]] + cent_diffs + [cent_diffs[-1]]

        for base_freq, (low_cents, high_cents) in zip(self.in_tune_freqs, pairwise(cent_diffs)):
            low_window = self.add_cents_to_freq(base_freq, -1 * low_cents)
            high_window = self.add_cents_to_freq(base_freq, high_cents)
            self.freq_scan_windows.append((low_window, high_window))

    def tune(self):
        p = pyaudio.PyAudio()

        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK_SIZE)

        while stream.is_active():
            self.check_queue()
            if self.quit_flag:
                break

            if self.pause_flag:
                time.sleep(0.1)
                continue

            binary_data = stream.read(self.CHUNK_SIZE)
            self.add_to_buffer(binary_data)
            self.match_freqs()
            self.send_note_info()

        stream.stop_stream()
        stream.close()
        p.terminate()

    def check_queue(self):
        while self.inbound_queue.qsize() > 0:
            message = self.inbound_queue.get()
            
            match message.message_type:
                case MessageToTunerType.PAUSE:
                    self.pause_flag = True
                case MessageToTunerType.RESUME:
                    self.pause_flag = False
                case MessageToTunerType.QUIT:
                    self.quit_flag = True
                case MessageToTunerType.SET_NOTES:
                    # Middle C is 9 semitones/900 cents below A4
                    self.middle_c_freq = Tuner.add_cents_to_freq(message.a4, -900)
                    self.set_freqs(message.notes)
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
        hps = hps/hps.max()
        freqs_hps = np.linspace(0, freqs[-1]/self.HPS_PARTIALS, len(freqs))

        if self.mode == TuningMode.MONOPHONIC:
            peak_locs = find_peaks(hps, threshold=self.HPS_THRESHOLD, distance=50)
            peak_freqs = freqs_hps[peak_locs[0]]
            if len(peak_freqs) > 0:
                self.matched_freqs = [peak_freqs[0]]

        else: # TuningMode.POLYPHONIC
            peak_locs = find_peaks(hps, threshold=self.HPS_THRESHOLD, distance=5)
            peak_freqs = freqs_hps[peak_locs[0]]
            peak_vals = hps[peak_locs[0]]

            self.matched_freqs = np.zeros(len(self.in_tune_freqs))

            for idx, base_freq in enumerate(self.in_tune_freqs):
                current_window  = self.freq_scan_windows[idx]
                candidate_locs  = np.where((peak_freqs > current_window[0]) & (peak_freqs < current_window[1]))
                candidate_freqs = peak_freqs[candidate_locs]
                candidate_vals  = peak_vals[candidate_locs]

                # evaluate each candidate based on a heuristic
                # only takes into account closeness to desired freq and relative power for now
                # could add something that looks at whether it's likely to be a harmonic of a lower note
                candidate_cent_diff = np.abs(Tuner.calc_cent_diff(base_freq, candidate_freqs))
                decay_rate = 0.01
                hps_heuristic = candidate_vals * decay_rate**(candidate_cent_diff/100)

                if len(hps_heuristic) > 0:
                    self.matched_freqs[idx] = candidate_freqs[np.argmax(hps_heuristic)]
                else:
                    self.matched_freqs[idx] = base_freq

    def add_to_buffer(self, binary_data):
        data = np.frombuffer(binary_data, dtype=np.int16)
        self.buffer = np.append(self.buffer, data)
        self.buffer = self.buffer[self.CHUNK_SIZE:]

    def send_note_info(self):
        message_data = []
        for freq in self.matched_freqs:
            message_data.append(self.calc_note_info(freq))
        message = MessageToGUI(MessageToGUIType.NOTE_DIFFS, message_data)
        self.outbound_queue.put(message)

    def calc_note_info(self, freq):
        cents_above_middle_c = self.calc_cent_diff(self.middle_c_freq, freq)
        note_number = round(cents_above_middle_c/100)
        cent_diff = cents_above_middle_c - (note_number*100)
        return (note_number, cent_diff)
