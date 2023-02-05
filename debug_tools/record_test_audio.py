import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Recording in progress")
frames = []
seconds = 1
for i in range(0, int(RATE / CHUNK * seconds)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Recording over")

stream.stop_stream()
stream.close()
p.terminate()

audio_buffer = b''.join(frames)
wf = wave.open("high_e_in_tune_1_sec.wav", 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(audio_buffer)
wf.close()

audio_array = np.frombuffer(audio_buffer, dtype=np.int16)
times = np.linspace(0, seconds, num=len(audio_array))

plt.plot(times, audio_array)
plt.xlim(0, seconds)
plt.xlabel('Time (s))')
plt.ylabel('Signal Wave')
plt.grid(True)
plt.show()