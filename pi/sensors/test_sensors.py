import asyncio
import pyaudio
import numpy as np

# Global array to store the last second of audio values
last_second_left = []
last_second_right = []

async def get_decibels(rate=48000, chunk=1024, device_index=1):
    global decibel_values

    p = pyaudio.PyAudio()
    list_input_device(p)
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=chunk)

    try:
        while True:
            data = await asyncio.to_thread(stream.read, chunk, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Separate left and right channels
            left_channel = audio_data[::2]
            right_channel = audio_data[1::2]

            last_second_left.append(left_channel)
            last_second_right.append(right_channel)

            if len(last_second_left) >= rate:
                # Compute RMS and convert to decibels
                left_rms = np.sqrt(np.mean(left_channel**2))
                right_rms = np.sqrt(np.mean(right_channel**2))

                left_db = 20 * np.log10(left_rms + 1e-6)  # Avoid log(0)
                right_db = 20 * np.log10(right_rms + 1e-6)

                print(f"Left: {left_db:.2f} dB, Right: {right_db:.2f} dB")

            await asyncio.sleep(rate / chunk)  # Update values approximately once per second

    except asyncio.CancelledError:
        stream.stop_stream()
        stream.close()
        p.terminate()
        raise

def list_input_device(p):
    nDevices = p.get_device_count()
    print('Found input devices:')
    for i in range(nDevices):
        deviceInfo = p.get_device_info_by_index(i)
        devName = deviceInfo['name']
        print(f"Device ID {i}: {devName}")

async def main():
    try:
        await get_decibels()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())
