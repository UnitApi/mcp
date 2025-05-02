#!/bin/bash
# client.sh - Starts the TTS client locally

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running. Please start Ollama first."
    echo "You can start Ollama by running: ollama serve"
    exit 1
fi

# Check if TTS server is running
if ! curl -s http://localhost:8081/tts -d '{"text":"test"}' > /dev/null; then
    echo "Warning: TTS server might not be running. Make sure to start it with server.sh"
    echo "Continuing anyway..."
fi

echo "Starting TTS client (Ollama weather forecast to speech)..."
python3 get_weather_from_ollama.py
