from matplotlib import pyplot
import numpy as np
import scipy.interpolate as spi
import scipy.signal as sps 
import statsmodels.api as sm 

from load_wav_file import load_wav_file

filename = "seven_string_drop_a_1_second.wav"

(signal, times, sample_freq) = load_wav_file(filename)

hanning_window = np.hanning(len(signal))
padded_signal = np.pad(signal * hanning_window, (0, len(signal) * 3), "constant")

(freqs, psd) = sps.periodogram(padded_signal, sample_freq, scaling='density')

psd = (psd-psd.min())/(psd.max() - psd.min())

pyplot.semilogy(freqs, psd)
pyplot.xlim(0, 350)
pyplot.xlabel('Time (s)')
pyplot.ylabel('Signal')
pyplot.grid(True)
pyplot.show()


partials = 3
spectra = []
psd_interp = spi.interp1d(freqs, psd, kind='nearest')
for n in range(1, partials + 1):
    freqs_interp = np.linspace(0, freqs[-1] * n/partials, num=len(freqs))
    s = psd_interp(freqs_interp)
    spectra.append(s) 

hps = np.product(np.abs(spectra), axis=0)
freqs_hps = np.linspace(0, freqs[-1]/partials, len(freqs))

peak_locs = sps.find_peaks(hps, threshold=10**-6)
peak_freqs = freqs_hps[peak_locs[0]]
print(peak_freqs)
pyplot.semilogy(freqs_hps, hps)
pyplot.xlim([20, 350])
pyplot.xlabel('Frequency (Hz)')
pyplot.ylabel('PSD [V**2/Hz]')
pyplot.title('Harmonic Product Spectrum, upsampled')
pyplot.grid(True)
pyplot.show()

a = 7