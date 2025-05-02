#!/bin/bash
# start_unitmcp_client.sh - Starts the UnitMCP client

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running. Please start Ollama first with ./start_ollama.sh"
    exit 1
fi

# Check if TTS server is running
if ! curl -s http://localhost:8081/tts -d '{"text":"test"}' > /dev/null; then
    echo "Warning: TTS server might not be running. Make sure to start it with ./start_tts_server.sh"
    echo "Continuing anyway..."
fi

# Check if STT server is running
if ! curl -s http://localhost:8082/stt -d '{"duration":1}' > /dev/null; then
    echo "Warning: STT server might not be running. Make sure to start it with ./start_stt_server.sh"
    echo "Continuing anyway..."
fi

echo "Starting UnitMCP client..."
python3 unitmcp_client.py "$@"
