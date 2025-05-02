# Minimal Ollama Setup for UnitMCP Testing

This directory contains scripts for setting up a minimal Ollama environment to test the UnitMCP protocol with text-to-speech and speech-to-text capabilities.

## Overview

The `install_minimal_ollama.sh` script sets up a complete environment for testing UnitMCP with:

1. **Text-to-Speech (TTS)**: Convert text to speech and play it on the computer's speakers
2. **Speech-to-Text (STT)**: Record audio from the microphone and convert it to text
3. **Ollama Integration**: Process text through the Ollama language model and speak the responses

## Components

The installation script creates the following components:

- **TTS Server**: Uses `pyttsx3` to convert text to speech (runs on port 8081)
- **STT Server**: Uses `SpeechRecognition` to convert speech to text (runs on port 8082)
- **Ollama Server**: Runs the tinyllama model for text processing (runs on port 11434)
- **UnitMCP Client**: Provides a unified interface to test all functionalities

## Installation

To install the minimal Ollama setup:

```bash
./install_minimal_ollama.sh
```

This script will:
1. Install required Python packages (pyttsx3, aiohttp, requests, SpeechRecognition, pyaudio)
2. Install Ollama if not already installed
3. Pull the tinyllama model (smallest available Ollama model)
4. Create all necessary Python scripts and shell scripts for testing

## Usage

After installation, you need to start each component in a separate terminal:

1. Start the Ollama server:
   ```bash
   ./start_ollama.sh
   ```

2. Start the TTS server:
   ```bash
   ./start_tts_server.sh
   ```

3. Start the STT server:
   ```bash
   ./start_stt_server.sh
   ```

4. Run the UnitMCP client:
   ```bash
   ./start_unitmcp_client.sh
   ```

## Client Modes

The UnitMCP client supports several modes of operation:

- **Full Demonstration Loop** (default):
  ```bash
  ./start_unitmcp_client.sh --mode full-loop
  ```
  This mode demonstrates the complete workflow: speaks a welcome message, records your speech, sends it to Ollama, and speaks the response.

- **Text-to-Speech**:
  ```bash
  ./start_unitmcp_client.sh --mode tts --text "Hello world"
  ```
  Converts the provided text to speech and plays it on the speakers.

- **Speech-to-Text**:
  ```bash
  ./start_unitmcp_client.sh --mode stt --duration 5
  ```
  Records audio for the specified duration (in seconds) and converts it to text.

- **Speech-to-Ollama**:
  ```bash
  ./start_unitmcp_client.sh --mode stt-ollama --duration 5 --prompt "Answer this question:"
  ```
  Records audio, converts it to text, sends it to Ollama with an optional prompt prefix, and displays the response.

- **Weather Forecast to Speech**:
  ```bash
  ./start_unitmcp_client.sh --mode weather-tts
  ```
  Asks Ollama for a weather forecast and speaks the response.

## Requirements

- Python 3
- Internet connection (for speech recognition and Ollama model download)
- Microphone (for speech-to-text functionality)
- Speakers (for text-to-speech functionality)

## Troubleshooting

- If you encounter issues with the `pyaudio` package installation, you may need to install PortAudio development headers:
  ```bash
  # On Ubuntu/Debian
  sudo apt-get install portaudio19-dev
  
  # On macOS
  brew install portaudio
  ```

- If Ollama fails to install, visit https://ollama.com for manual installation instructions.

- The speech recognition functionality requires an internet connection as it uses Google's Speech Recognition API.
