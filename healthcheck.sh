#!/bin/bash

# Path to log file
LOG_FILE="/app/healthcheck.log"

# Check if the log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Healthcheck log file not found!"
    exit 1
fi

# Check for the most recent healthcheck messages
if grep -q "HEALTHCHECK: MQTT connection successfully established." $LOG_FILE && \
   grep -q "HEALTHCHECK: Serial connection successfully established." $LOG_FILE; then
    echo "Healthcheck passed"
    exit 0
else
    echo "Healthcheck failed"
    exit 1
fi
