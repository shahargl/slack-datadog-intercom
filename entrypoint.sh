#!/usr/bin/env bash

# Cloud Run needs incoming port
echo "Starting the simple http server on port 8080"
python -m http.server 8080 &
# Start the actual application
echo "Starting the slack bot"
python app.py