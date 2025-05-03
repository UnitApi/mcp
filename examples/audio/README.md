# UnitMCP Audio Examples

This directory contains examples demonstrating audio recording, playback, and processing capabilities of the UnitMCP framework.

## Files in This Directory

- `audio_record.py` - Example for recording and playing back audio
- `tts_example.py` - Example for text-to-speech functionality
- `audio_processing.py` - Example for audio effects and processing
- `server.py` - Server implementation for remote audio processing
- `client.py` - Client implementation for connecting to the server
- `runner.py` - Unified runner script to manage both client and server components
- `config/` - Directory containing configuration files:
  - `client.yaml` - Client configuration settings
  - `server.yaml` - Server configuration settings

## Available Examples

### Audio Recording and Playback

The `audio_record.py` example demonstrates basic audio recording and playback functionality:

```bash
# Run the audio recording example
python audio_record.py

# Run with custom settings
python audio_record.py --duration 5 --rate 44100
```

This example shows how to:
- Initialize audio input and output devices
- Record audio from a microphone
- Save recordings to WAV files
- Play back recorded or stored audio
- Adjust volume and audio settings

### Text-to-Speech Integration

The audio examples also demonstrate text-to-speech capabilities:

```bash
# Run the TTS example
python tts_example.py

# Generate speech from text
python tts_example.py --text "Hello, this is UnitMCP speaking"
```

This example showcases:
- Converting text to speech using different TTS engines
- Saving generated speech to audio files
- Streaming TTS output directly to audio devices
- Adjusting voice parameters (pitch, rate, volume)

## Using the Runner

The `runner.py` script provides a standardized way to start and manage both client and server components:

```bash
# Run both client and server with default configuration
python runner.py

# Run only the server
python runner.py --server-only

# Run only the client with audio recording
python runner.py --client-only --demo record

# Run only the client with TTS example
python runner.py --client-only --demo tts

# Specify custom configuration files
python runner.py --server-config config/custom_server.yaml --client-config config/custom_client.yaml

# Enable verbose logging
python runner.py --verbose
```

### Environment Configuration

The runner and example scripts can be configured using:

1. **Environment Variables (.env file)**: Create a `.env` file in the example directory with configuration values:

```
# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
LOG_LEVEL=INFO

# Audio configuration
AUDIO_DEVICE=default
SAMPLE_RATE=44100
CHANNELS=1
BIT_DEPTH=16
BUFFER_SIZE=1024
```

2. **Command Line Arguments**: Pass configuration values directly to the runner:

```bash
# Configure server host and port
SERVER_HOST=192.168.1.100 SERVER_PORT=8888 python runner.py

# Configure audio settings
SAMPLE_RATE=48000 CHANNELS=2 python runner.py --client-only --demo record
```

3. **Configuration Files**: Specify custom YAML configuration files:

```bash
python runner.py --server-config config/custom_server.yaml
```

The configuration precedence is: Command Line > .env File > Default Configuration Files

## Audio Processing Features

The UnitMCP audio module provides several audio processing capabilities:

### 1. Audio Recording

```python
# Example audio recording
from unitmcp.audio import AudioRecorder

# Create recorder
recorder = AudioRecorder(sample_rate=44100, channels=1)

# Start recording
recorder.start()

# Record for 5 seconds
import time
time.sleep(5)

# Stop and save recording
audio_data = recorder.stop()
recorder.save_to_file(audio_data, "recording.wav")
```

### 2. Audio Playback

```python
# Example audio playback
from unitmcp.audio import AudioPlayer

# Create player
player = AudioPlayer()

# Play audio file
player.play_file("recording.wav")

# Play raw audio data
player.play_data(audio_data)
```

### 3. Audio Processing

```python
# Example audio processing
from unitmcp.audio import AudioProcessor

# Create processor
processor = AudioProcessor()

# Apply effects
processed_audio = processor.apply_effect(audio_data, "echo", delay=0.5, decay=0.5)
processor.save_to_file(processed_audio, "processed.wav")
```

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- Audio dependencies: PyAudio, SoundDevice, and NumPy
- For TTS examples: pyttsx3 or gTTS

Install the required dependencies:
```bash
pip install pyaudio sounddevice numpy pyttsx3 gtts
```

## Hardware Requirements

For optimal audio experience, you'll need:

- Microphone (for recording examples)
- Speakers or headphones (for playback examples)
- Audio interface (optional, for higher quality recording)

## Configuration

Audio examples can be configured using environment variables or command-line arguments:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `AUDIO_DEVICE` | Audio device index or name | System default |
| `SAMPLE_RATE` | Sample rate in Hz | 44100 |
| `CHANNELS` | Number of audio channels | 1 (mono) |
| `BIT_DEPTH` | Bit depth for recording | 16 |
| `BUFFER_SIZE` | Audio buffer size | 1024 |

## Additional Resources

- [UnitMCP Audio API Documentation](../../docs/api/audio.md)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)
- [SoundDevice Documentation](https://python-sounddevice.readthedocs.io/)
