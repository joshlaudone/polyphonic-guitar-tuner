from matplotlib import pyplot
import numpy as np
import scipy.interpolate as spi
import scipy.signal as sps 
import statsmodels.api as sm 
from math import log2

from load_wav_file import load_wav_file

filename = "seven_string_drop_a_1_second.wav"

(signal, times, sample_freq) = load_wav_file(filename)

hanning_window = np.hanning(len(signal))
padded_signal = np.pad(signal * hanning_window, (0, len(signal) * 3), "constant")

(freqs, psd) = sps.periodogram(padded_signal, sample_freq, scaling='density')


# pyplot.semilogy(freqs, psd)
# pyplot.xlim(0, 350)
# pyplot.xlabel('Time (s)')
# pyplot.ylabel('Signal')
# pyplot.grid(True)
# pyplot.show()

partials = 3
min_thresh = 10**-4
spectra = []
psd_interp = spi.interp1d(freqs, psd, kind='nearest')
for n in range(1, partials + 1):
    freqs_interp = np.linspace(0, freqs[-1] * n/partials, num=len(freqs))
    s = psd_interp(freqs_interp)
    spectra.append(s) 

hps = np.product(np.abs(spectra), axis=0)
freqs_hps = np.linspace(0, freqs[-1]/partials, len(freqs))
hps = hps/hps.max()


peak_locs = sps.find_peaks(hps, threshold=min_thresh, distance=5)
peak_freqs = freqs_hps[peak_locs[0]]
peak_hps = hps[peak_locs[0]]
for pf,ph in zip(peak_freqs, peak_hps):
    if pf > 350:
        break
    print("%03.2f\t%.2E" % (pf,ph))
pyplot.semilogy(freqs_hps, hps)
pyplot.xlim([20, 350])
pyplot.ylim([min_thresh, 1])
pyplot.xlabel('Frequency (Hz)')
pyplot.ylabel('PSD [V**2/Hz]')
pyplot.title('Harmonic Product Spectrum, upsampled')
pyplot.grid(True)
pyplot.show()

desired_freq = 146.83
decay_rate = 0.01
abs_cent_diff = np.abs(1200 * np.log2(freqs_hps/146.83))

hps_heuristic = hps * decay_rate**(abs_cent_diff/100)

pyplot.semilogy(freqs_hps, hps_heuristic)
pyplot.xlim([20, 350])
pyplot.ylim([10**-8, 1])
pyplot.xlabel('Frequency (Hz)')
pyplot.ylabel('PSD [V**2/Hz]')
pyplot.title('Harmonic Product Spectrum Heuristic')
pyplot.grid(True)
pyplot.show()