#!/bin/bash

# Name of the Python script
PYTHON_SCRIPT="time_dialation.py"

# Log file for output
LOG_FILE="output.log"

# Run the Python script with nohup
nohup python3 $PYTHON_SCRIPT > $LOG_FILE &

# Print the PID of the background process
echo "Script is running in the background with PID $!"