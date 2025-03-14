import serial
import time

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

def benchmark_serial(port: str, baudrate: int = 19200, duration: int = 10):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        
        start_time = time.time()
        end_time = start_time + duration
        count = 0  # Track successful send/read cycles

        while time.time() < end_time:
            get_arduino_data(ser)
            
            if line:  # If data is received, count it
                count += 1

        elapsed_time = time.time() - start_time
        rate = count / elapsed_time  # Calculate cycles per second
        print(f"Completed {count} cycles in {elapsed_time:.2f} seconds.")
        print(f"Rate: {rate:.2f} cycles per second.")

    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    port = "/dev/ttyACM0"  # Change this as needed (e.g., COM3 on Windows)
    benchmark_serial(port)

