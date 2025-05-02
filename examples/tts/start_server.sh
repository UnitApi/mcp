#!/bin/bash
# server.sh - Starts the TTS server locally

echo "Starting TTS server on http://localhost:8081/tts"
echo "Press Ctrl+C to stop the server"

# Run the TTS server
python3 server.py
