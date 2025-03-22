import time
import os
from gpiozero import Button

# Define RPM sensors
SENSORS = {
    "TOP": Button(17),
    "RIGHT": Button(27),
    "BOTTOM": Button(22),
    "LEFT": Button(23)
}

sensor_states = {name: 0 for name in SENSORS}

def update_sensor_state(sensor_name):
    sensor_states[sensor_name] = 1

def reset_sensor_states():
    for name in sensor_states:
        sensor_states[name] = 0

# Attach event handlers
for name, sensor in SENSORS.items():
    sensor.when_pressed = lambda name=name: update_sensor_state(name)

def display_sensors():
    """ Continuously display the current state of all RPM sensors. """
    try:
        while True:
            reset_sensor_states()
            os.system('clear')  # Use 'cls' on Windows
            for name, state in sensor_states.items():
                print(f"{name}: {'TRIGGERED' if state else 'NOT TRIGGERED'}")
            time.sleep(0.01)  # Update as fast as possible
    except KeyboardInterrupt:
        print("\nSensor monitoring stopped.")

if __name__ == "__main__":
    display_sensors()
