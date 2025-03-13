import serial
import time

def benchmark_serial(port: str, baudrate: int = 19200, duration: int = 10):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        
        start_time = time.time()
        end_time = start_time + duration
        count = 0  # Track successful send/read cycles

        while time.time() < end_time:
            ser.write(b'\x00')  # Send a zero byte
            line = ser.readline().strip()  # Read response
            
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

