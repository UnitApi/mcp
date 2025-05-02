#!/bin/bash
# start_stt_server.sh - Starts the STT server

echo "Starting STT server on http://localhost:8082/stt"
echo "Press Ctrl+C to stop the server"

# Run the STT server
python3 stt_server.py
