import serial
import sys
import termios
import tty
import threading
import time

def read_serial(ser):
    """Continuously read from the serial port and print received data as a list of integers."""
    data = ser.readline().strip()
    if len(data) % 2 != 0:
        return
    
    int_list = []
    for i in range(0, len(data), 2):
        high_byte = data[i]
        low_byte = data[i + 1]
        int_value = (high_byte << 8) | low_byte
        int_list.append(int_value)
    
    if int_list:
        print(f"Received: {int_list}")

def serial_monitor(port: str, baudrate: int = 19200):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        
        print("Serial monitor started")
        while True:
            ser.write(b'\x00')
            read_serial(ser)
            time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    port = "/dev/ttyACM0"  # Change this as needed (e.g., COM3 on Windows)
    serial_monitor(port)
