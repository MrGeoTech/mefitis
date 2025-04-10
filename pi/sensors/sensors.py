from gpiozero import Button
from math import log10
from w1thermsensor import AsyncW1ThermSensor, Unit

import RPi.GPIO as GPIO
import asyncio
import numpy as np
import psycopg2
import pyaudio
import serial as s
import statistics
import time

# PostgreSQL Database Configuration
DB_CONFIG = {
    "dbname": "data",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

# Constants
MICROSECONDS_PER_MINUTE = 60 * 1000 * 1000

# Sensors should be wired as following:
# TOP    -> GPIO 17 (PIN 11)
# RIGHT  -> GPIO 27 (PIN 13)
# BOTTOM -> GPIO 22 (PIN 15)
# LEFT   -> GPIO 23 (PIN 16)
SENSORS = {
    "TOP": Button(17),
    #"RIGHT": Button(27),
    #"BOTTOM": Button(22),
    #"LEFT": Button(23)
}

temp_data = [0, 0]
last_time = None
rpm = 0

p = pyaudio.PyAudio()
WIDTH = 2
CHANNELS = 2
RATE = int(p.get_default_input_device_info()['defaultSampleRate'])
DEVICE = p.get_default_input_device_info()['index']
max_db = 120;

accum_left = []
accum_right = []

def callback(in_data, frame_count, time_info, status):
    global accum_left, accum_right
    # Split stereo data into left and right mono streams
    
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    audio_float = audio_data.astype(np.float32) / 32767

    # Split stereo data into left and right channels
    left = audio_float[::2]
    right = audio_float[1::2]

    # Append DB to global list
    accum_left.extend(left)
    accum_right.extend(right)

    return in_data, pyaudio.paContinue

def calculate_rpm():
    global last_time
    global rpm
    current_time = int(time.time_ns() / 1000)
    
    if last_time is not None:
        time_diff = current_time - last_time
        if time_diff >= 10: # Debouncing
            rpm = (MICROSECONDS_PER_MINUTE / time_diff) / len(SENSORS) # Convert to RPM
        else:
            return # Keep last_time the same
    
    last_time = current_time

def init_db():
    """Initialize the PostgreSQL database and create the necessary table if it doesn't exist."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id SERIAL PRIMARY KEY,
            Sound_Engine REAL,
            Sound_Operator REAL,
            Emissions_Engine REAL,
            Emissions_Operator REAL,
            Temp_Engine REAL,
            Temp_Exhaust REAL,
            RPM INTEGER
        )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database initialization error: {e}")

def save_to_db(data):
    """Save aggregated data to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data (Sound_Engine, Sound_Operator, Emissions_Engine, Emissions_Operator, Temp_Engine, Temp_Exhaust, RPM)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database insert error: {e}")

async def update_temp_data():
    """Asynchronously update global temperature data."""
    global temp_data
    sensors = AsyncW1ThermSensor.get_available_sensors()
    while True:
        new_temp_data = temp_data.copy()  # Keep previous values in case of error
        for i, sensor in enumerate(sensors):
            try:
                temp = await sensor.get_temperature(Unit.DEGREES_C)
                new_temp_data[i] = temp
            except Exception as e:
                print(f"Temp Sensor Error: {e}")
        temp_data = new_temp_data
        await asyncio.sleep(1)

def get_arduino_data(serial):
    """Read a line from the Arduino and parse it into a list of integers."""
    serial.write(b'\x00')
    data = serial.readline().strip()
    
    if len(data) % 2 != 0:
        return []

    int_list = []
    for i in range(0, len(data), 2):
        high_byte = data[i]
        low_byte = data[i + 1]
        int_value = (high_byte << 8) | low_byte
        int_list.append(int_value)

    return int_list

def aggregate_data(sensor_buffer):
    """Compute the average of collected sensor data over the past second."""
    avg_data = [sum(col) / len(col) for col in zip(*sensor_buffer)]
    return avg_data

def get_average_db():
    global accum_left, accum_right

    if not accum_left or not accum_right:
        return [float('-inf'), float('-inf')]  # No audio data

    # Convert to NumPy arrays for efficient processing
    left_array = np.array(accum_left, dtype=np.float32)
    right_array = np.array(accum_right, dtype=np.float32)

    # Compute RMS
    rms_left = np.sqrt(np.mean(left_array ** 2))
    rms_right = np.sqrt(np.mean(right_array ** 2))

    # Convert RMS to decibels (as Python floats)
    def rms_to_db(rms):
        return float(20 * np.log10(rms)) if rms > 0 else float('-inf')

    left_db = float(rms_left) * 100 #rms_to_db(rms_left)
    right_db = float(rms_right) * 100 #rms_to_db(rms_right)

    # Clear the accumulators
    accum_left = []
    accum_right = []

    return [max_db + left_db, max_db + right_db]

async def main():
    try:
        init_db()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach the same event handler to all sensors
        for sensor in SENSORS.values():
            sensor.when_pressed = calculate_rpm

        # Initialize Serial Connection
        #serial = s.Serial('/dev/ttyACM0', baudrate=19200, timeout=1)
        
        asyncio.create_task(update_temp_data())
        
        sensor_buffer = []  # Store 100 readings (10ms * 100 = 1s)
        iterations = 0

        print(p.get_default_input_device_info())
        stream = p.open(format=p.get_format_from_width(WIDTH),
                        input_device_index=DEVICE,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=False,
                        stream_callback=callback)
        
        stream.start_stream()
        
        while True:
            try:
                arduino_data = [0,0,0,0]#get_arduino_data(serial)  # Returns a list [sensor1, sensor2, sensor3, ...]
                
                if len(temp_data) != 2 or len(arduino_data) != 4:
                    continue  # Skip iteration if data is incomplete

                sound_data = get_average_db()
                emissions_data = arduino_data[2:4]
                rpm_data = rpm  # Single integer

                # Collect sensor readings
                sensor_buffer.append(sound_data + emissions_data + temp_data + [rpm])

                # Check if 1 second has passed
                if iterations == 100:
                    if sensor_buffer:
                        # Aggregate and store in the database
                        aggregated = aggregate_data(sensor_buffer)
                        save_to_db(aggregated)

                        # Reset buffer
                        sensor_buffer = []
                        iterations = 0

                await asyncio.sleep(0.01)  # 10ms delay
                iterations += 1

            except Exception as e:
                print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'serial' in locals() and serial.is_open:
            serial.close()
        if 'stream' in locals() and stream.is_active():
            stream.stop_stream()
            stream.close()
        if 'p' in locals():
            p.terminate()

if __name__ == "__main__":
    asyncio.run(main())

