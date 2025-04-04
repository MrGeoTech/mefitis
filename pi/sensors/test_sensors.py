import asyncio
import pyaudio
import numpy as np

# Global array to store decibel values
decibel_values = []

async def get_decibels(rate=48000, chunk=1024):
    global decibel_values
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    try:
        while True:
            data = await asyncio.to_thread(stream.read, chunk)
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Separate left and right channels
            left_channel = audio_data[::2]
            right_channel = audio_data[1::2]
            
            # Compute RMS and convert to decibels
            left_rms = np.sqrt(np.mean(left_channel**2))
            right_rms = np.sqrt(np.mean(right_channel**2))
            
            left_db = 20 * np.log10(left_rms + 1e-6)  # Avoid log(0)
            right_db = 20 * np.log10(right_rms + 1e-6)
            
            decibel_values.append((left_db, right_db))
            await asyncio.sleep(1)  # Update values approximately once per second
    
    except asyncio.CancelledError:
        stream.stop_stream()
        stream.close()
        p.terminate()
        raise

async def main():
    task = asyncio.create_task(get_decibels())
    try:
        while True:
            if decibel_values:
                left_db, right_db = decibel_values[-1]
                print(f"Left: {left_db:.2f} dB, Right: {right_db:.2f} dB")
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        task.cancel()
        await task

if __name__ == "__main__":
    asyncio.run(main())
