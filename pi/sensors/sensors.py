import time
import psycopg2
import serial as s
from w1thermsensor import W1ThermSensor

# PostgreSQL Database Configuration
DB_CONFIG = {
    "dbname": "data",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

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

def get_temp_data():
    """Get temperature data from all available W1 sensors."""
    if W1ThermSensor.get_available_sensors() == []:
        return [0, 0]
    return [sensor.get_temperature() for sensor in W1ThermSensor.get_available_sensors()]

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

def get_rpm_data():
    """Placeholder for RPM sensor reading."""
    return 0  # TODO: Implement RPM reading logic

def aggregate_data(sensor_buffer):
    """Compute the average of collected sensor data over the past second."""
    avg_data = [sum(col) / len(col) for col in zip(*sensor_buffer)]
    return avg_data

def main():
    try:
        init_db()

        # Initialize Serial Connection
        serial = s.Serial('/dev/ttyACM0', baudrate=19200, timeout=1)
        
        sensor_buffer = []  # Store 100 readings (10ms * 100 = 1s)
        iterations = 0
        
        while True:
            try:
                temp_data = get_temp_data()  # Returns a list [temp1, temp2]
                arduino_data = get_arduino_data(serial)  # Returns a list [sensor1, sensor2, sensor3, ...]
                rpm_data = get_rpm_data()  # Single integer
                
                if len(temp_data) != 2 or len(arduino_data) != 4:
                    continue  # Skip iteration if data is incomplete

                # Collect sensor readings
                sensor_buffer.append(arduino_data[:4] + [temp_data[0], temp_data[1], rpm_data])

                # Check if 1 second has passed
                if iterations == 100:
                    if sensor_buffer:
                        # Aggregate and store in the database
                        aggregated = aggregate_data(sensor_buffer)
                        save_to_db(aggregated)

                        # Reset buffer
                        sensor_buffer = []
                        iterations = 0

                time.sleep(0.01)  # 10ms delay
                iterations += 1

            except Exception as e:
                print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'serial' in locals() and serial.is_open:
            serial.close()

if __name__ == "__main__":
    main()
