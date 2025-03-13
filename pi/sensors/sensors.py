import time
import sqlite3
import serial
from w1thermsensor import W1ThermSensor

# Initialize Serial Connection
arduino_serial = serial.Serial('/dev/ttyACM0',
                               baudrate=115200,
                               parity=serial.PARITY_NONE,
                               stopbits=serial.STOPBITS_ONE)

# Database setup
DB_NAME = "../data.db"

def init_db():
    """Initialize the SQLite database and create the necessary table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.close()

def save_to_db(data):
    """Save aggregated data to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_data (timestamp, sound_engine, sound_operator, emissions_engine, emissions_operator temp_engine, temp_exhaust, rpm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def get_temp_data():
    """Get temperature data from all available W1 sensors."""
    if W1ThermSensor.get_available_sensors() == None:
        return [0, 0]
    return [sensor.get_temperature() for sensor in W1ThermSensor.get_available_sensors()]

def get_arduino_data():
    """Read a line from the Arduino and parse it into a list of integers."""
    data = []
    in = arduino_serial.read()
    while in != '\n':
        in = arduino_serial.read()
    data.remove(data.length - 1)
    int_list = []
    
    if len(data) % 2 != 0:
        return []  # Malformed data

    for i in range(0, len(data), 2):
        high_byte = data[i]
        low_byte = data[i + 1]
        int_value = (high_byte << 8) | low_byte
        int_list.append(int_value)

    return int_list

def get_rpm_data():
    """Placeholder for RPM sensor reading."""
    return 0  # TODO: Implement RPM reading logic

def aggregate_data(sensor_buffer):
    """Compute the average of collected sensor data over the past second."""
    avg_data = [sum(col) / len(col) for col in zip(*sensor_buffer)]
    return avg_data

def main():
    init_db()
    
    sensor_buffer = []  # Store 100 readings (10ms * 100 = 1s)
    last_save_time = time.time()
    
    while True:
        try:
            temp_data = get_temp_data()  # Returns a list [temp1, temp2]
            arduino_data = get_arduino_data()  # Returns a list [sensor1, sensor2, sensor3, ...]
            rpm_data = get_rpm_data()  # Single integer
            
            if len(temp_data) != 2 or len(arduino_data) != 4:
                continue  # Skip iteration if data is incomplete

            # Collect sensor readings
            sensor_buffer.append(arduino_data[:4] + [temp_data[0], temp_data[1], rpm_data])

            # Check if 1 second has passed
            if time.time() - last_save_time >= 1.0:
                if sensor_buffer:
                    # Aggregate and store in the database
                    aggregated = aggregate_data(sensor_buffer)
                    timestamp = int(time.time())  # Unix timestamp
                    save_to_db([timestamp] + aggregated)

                    # Reset buffer
                    sensor_buffer = []
                    last_save_time = time.time()

            time.sleep(0.01)  # 10ms delay

        except Exception as e:
            raise e

if __name__ == "__main__":
    main()
