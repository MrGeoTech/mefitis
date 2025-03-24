#!/bin/bash
# NOTE: This should be run in the shell.nix environment

# Start webserver/webserver.js
pushd webserver > /dev/null
deno run --allow-env --allow-read --allow-write --allow-net webserver.ts &
WEBSERVER_PID=$!
popd > /dev/null

# Start sensors/measurements.py
pushd sensors > /dev/null
sudo python sensors.py &
SENSOR_PID=$!
popd > /dev/null

# Function to clean up on exit
cleanup() {
    echo "Stopping processes..."
    kill $SENSOR_PID $WEBSERVER_PID
    wait $SENSOR_PID $WEBSERVER_PID 2>/dev/null
    echo "Shutdown complete."
}

# Trap SIGINT and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM

# Wait for processes to exit
wait
