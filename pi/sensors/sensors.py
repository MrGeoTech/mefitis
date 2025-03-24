import time
import psycopg2
import serial as s
import asyncio
from w1thermsensor import AsyncW1ThermSensor, Unit
from gpiozero import Button
import RPi.GPIO as GPIO
import numpy as np

# PostgreSQL Database Configuration
DB_CONFIG = {
    "dbname": "data",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

# Constants
NUM_MAGNETS = 4  # Number of sensors/magnets
NANOSECONDS_PER_MINUTE = 60 * 1000 * 1000 * 1000

# Sensors should be wired as following:
# TOP    -> GPIO 17 (PIN 11)
# RIGHT  -> GPIO 27 (PIN 13)
# BOTTOM -> GPIO 22 (PIN 15)
# LEFT   -> GPIO 23 (PIN 16)
SENSORS = {
    "TOP": Button(17),
    "RIGHT": Button(27),
    "BOTTOM": Button(22),
    "LEFT": Button(23)
}

temp_data = [0, 0]
last_time = None
rpm = 0

def calculate_rpm():
    global last_time
    current_time = time.time_ns()
    
    if last_time is not None:
        time_diff = current_time - last_time
        if time_diff > 0:
            rpm = (NANOSECONDS_PER_MINUTE / time_diff) / NUM_MAGNETS  # Convert to RPM
    
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

def sensor_to_db(sensor_value, ref_value=50, ref_db=61, full_scale=1023):
    """
    Convert sensor readings to decibels using logarithmic scaling.

    :param sensor_value: The raw sensor reading (0-1023)
    :param ref_value: A known sensor value corresponding to a known dB level
    :param ref_db: The dB level corresponding to ref_value
    :param full_scale: The maximum sensor reading
    :return: Estimated decibel level
    """
    if sensor_value <= 0:
        return float('-inf')  # Log(0) is undefined, treat it as very low dB

    # Calculate scale factor A using the reference point
    A = ref_db / np.log10(ref_value)

    # Compute the dB level for the given sensor value
    dB = A * np.log10(sensor_value)
    
    return dB

def aggregate_data(sensor_buffer):
    """Compute the average of collected sensor data over the past second."""
    avg_data = [sum(col) / len(col) for col in zip(*sensor_buffer)]
    return avg_data

async def main():
    try:
        init_db()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Attach the same event handler to all sensors
        for sensor in SENSORS.values():
            sensor.when_pressed = calculate_rpm

        # Initialize Serial Connection
        serial = s.Serial('/dev/ttyACM0', baudrate=19200, timeout=1)
        
        asyncio.create_task(update_temp_data())
        
        sensor_buffer = []  # Store 100 readings (10ms * 100 = 1s)
        iterations = 0
        
        while True:
            try:
                arduino_data = get_arduino_data(serial)  # Returns a list [sensor1, sensor2, sensor3, ...]
                sound_data = [sensor_to_db(arduino_data[0]), sensor_to_db([1])]
                emissions_data = arduino_data[2:4]
                rpm_data = rpm  # Single integer
                
                if len(temp_data) != 2 or len(arduino_data) != 4:
                    continue  # Skip iteration if data is incomplete

                # Collect sensor readings
                sensor_buffer.append()

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

if __name__ == "__main__":
    asyncio.run(main())
