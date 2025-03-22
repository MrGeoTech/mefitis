import time
import os
from gpiozero import Button

# Define RPM sensors
SENSORS = {
    "TOP": Button(17, pull_up=True),
    "RIGHT": Button(27, pull_up=True),
    "BOTTOM": Button(22, pull_up=True),
    "LEFT": Button(23, pull_up=True)
}

def display_sensors():
    """ Continuously display the current state of all RPM sensors. """
    try:
        while True:
            os.system('clear')  # Use 'cls' on Windows
            for name, sensor in SENSORS.items():
                state = "TRIGGERED" if sensor.is_pressed else "NOT TRIGGERED"
                print(f"{name}: {state}")
            time.sleep(0.01)  # Update as fast as possible
    except KeyboardInterrupt:
        print("\nSensor monitoring stopped.")

if __name__ == "__main__":
    display_sensors()
