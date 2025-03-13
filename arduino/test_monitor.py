import serial

def read_serial(port: str, baudrate: int = 9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Reading from {port} at {baudrate} baud...")
        
        while True:
            line = ser.readline().strip()  # Read a line and remove whitespace
            if line:
                integers = []
                for i in range(0, len(line), 2):
                    if i + 1 < len(line):
                        value = (line[i] << 8) | line[i + 1]  # Combine HighByte and LowByte
                        integers.append(str(value))
                print(",".join(integers))
    
    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    port = "/dev/ttyACM0"  # Change this to match your system (e.g., COM3 on Windows)
    read_serial(port)
