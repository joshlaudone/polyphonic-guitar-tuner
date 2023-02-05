from typing import Tuple

import numpy as np
from wave import open

def load_wav_file(filename: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    file = open(filename, 'rb')
    sample_freq = file.getframerate()
    frames = file.getnframes()
    signal_buffer = file.readframes(-1)

    file.close()

    signal = np.frombuffer(signal_buffer, dtype=np.int16)
    times = np.linspace(0, frames / sample_freq, frames)

    return (signal, times, sample_freq)