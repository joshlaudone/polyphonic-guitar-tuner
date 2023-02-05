import pyaudio
import numpy as np
import scipy.signal as signal
import time
import struct
import matplotlib.pyplot as plt

# Constants
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 2**13

p = pyaudio.PyAudio();

full_data = np.array([])
count = 0

def callback(in_data, frame_count, time_info, status):
    global full_data, count
    count += 1
    

    audio_data = np.frombuffer(in_data, dtype=np.float32)
    full_data=np.append(full_data, audio_data)
    return (audio_data, pyaudio.paContinue)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                stream_callback=callback,
                frames_per_buffer=CHUNK)


stream.start_stream()

time.sleep(2)
stream.stop_stream()
stream.close()
p.terminate()

print(count)
plt.plot(full_data)
plt.show()