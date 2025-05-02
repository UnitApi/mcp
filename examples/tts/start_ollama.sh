#!/bin/bash
# start_ollama.sh - Starts the Ollama server

echo "Starting Ollama server on http://localhost:11434"
echo "Press Ctrl+C to stop the server"

# Run Ollama
ollama serve
