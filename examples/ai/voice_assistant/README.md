# Voice Assistant Example

This example demonstrates how to build a voice assistant using UnitMCP's AI capabilities. The assistant can:

1. Listen for voice commands
2. Convert speech to text
3. Process natural language commands
4. Generate responses using a language model
5. Convert text responses to speech
6. Control hardware devices based on commands

## Architecture

The example uses a client-server architecture:

- **Client**: Handles audio input/output and user interaction
- **Server**: Processes commands, runs AI models, and controls hardware

## Components

- `runner.py`: Sets up and runs both client and server
- `client.py`: Handles audio recording, playback, and user interface
- `server.py`: Processes commands and runs AI models
- `config/`: Configuration files for the example

## Hardware Requirements

- Microphone (for speech input)
- Speakers (for speech output)
- Optional: Raspberry Pi or other hardware for physical device control

## Running the Example

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the example by editing the files in the `config/` directory.

3. Run the complete example:

```bash
python runner.py
```

Or run the client and server separately:

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py
```

## Usage

1. Say "Hey Assistant" to activate the voice assistant
2. Ask a question or give a command
3. The assistant will respond with voice and text

Example commands:
- "What's the weather like today?"
- "Turn on the living room lights"
- "Tell me a joke"
- "What time is it?"

## Customization

You can customize the assistant by:

1. Modifying the wake word in `config/client.yaml`
2. Adding new commands in `server.py`
3. Changing the language model in `config/server.yaml`
4. Adjusting TTS settings in `config/server.yaml`
