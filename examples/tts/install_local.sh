#!/bin/bash
# install_local.sh - Installs TTS server locally and Ollama

echo "Installing TTS server and Ollama locally..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip install pyttsx3 aiohttp requests

# Check if Ollama is already installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    # Install Ollama using the official installation script
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Check if installation was successful
    if ! command -v ollama &> /dev/null; then
        echo "Failed to install Ollama. Please install it manually from https://ollama.com"
        exit 1
    fi
else
    echo "Ollama is already installed."
fi

# Pull the tinyllama model (used in the client)
echo "Pulling the tinyllama model for Ollama..."
ollama pull tinyllama

echo "Installation completed successfully!"
echo "To start the TTS server, run: ./server.sh"
echo "To start the Ollama client, run: ./client.sh"
echo "Make sure Ollama is running before starting the client."
