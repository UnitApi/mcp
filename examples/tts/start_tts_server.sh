#!/bin/bash
# start_tts_server.sh - Starts the TTS server

echo "Starting TTS server on http://localhost:8081/tts"
echo "Press Ctrl+C to stop the server"

# Run the TTS server
python3 server.py
