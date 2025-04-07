import pyaudio
import time
from math import log10
import audioop

p = pyaudio.PyAudio()
WIDTH = 2
CHANNELS = 2
RATE = int(p.get_default_input_device_info()['defaultSampleRate'])
DEVICE = p.get_default_input_device_info()['index']

rms_left = 1
rms_right = 1
print(p.get_default_input_device_info())

def callback(in_data, frame_count, time_info, status):
    global rms_left, rms_right
    #print(in_data)
    #print("-" * 20)
    # Split stereo data into left and right mono streams
    left = audioop.tomono(in_data, WIDTH, 1, 0)
    right = audioop.tomono(in_data, WIDTH, 0, 1)

    #print(left)
    #print(right)
    #print("-" * 30)
    
    # Calculate RMS for each channel
    rms_left = audioop.rms(left, WIDTH) / 32767
    rms_right = audioop.rms(right, WIDTH) / 32767
    return in_data, pyaudio.paContinue

stream = p.open(format=p.get_format_from_width(WIDTH),
                input_device_index=DEVICE,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=False,
                stream_callback=callback)

stream.start_stream()

while stream.is_active():
    db_left = 20 * log10(rms_left) if rms_left > 0 else -float('inf')
    db_right = 20 * log10(rms_right) if rms_right > 0 else -float('inf')
    print(f"Left  - RMS: {rms_left:.4f}  DB: {db_left:.2f}")
    print(f"Right - RMS: {rms_right:.4f}  DB: {db_right:.2f}")
    print("-" * 40)
    time.sleep(0.3)

stream.stop_stream()
stream.close()
p.terminate()
