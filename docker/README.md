# Virtual Hardware Control with LLM in Docker

This directory contains a Docker Compose setup for testing hardware control with Large Language Models (LLMs) in a virtual environment. The setup includes:

1. A virtual hardware server that simulates hardware devices like GPIO, camera, and audio
2. An Ollama LLM server for natural language processing
3. A client that connects to both the hardware server and the LLM to enable natural language control of virtual hardware

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic knowledge of Docker and containerization
- Understanding of the UnitMCP hardware control system

## Directory Structure

```
docker/
├── client/                 # Client container files
│   ├── Dockerfile          # Client container definition
│   └── llm_client.py       # LLM client implementation
├── server/                 # Server container files
│   ├── Dockerfile          # Server container definition
│   └── hardware_server.py  # Virtual hardware server implementation
└── README.md               # This file
```

## Getting Started

### 1. Build and Start the Containers

From the root directory of the project, run:

```bash
docker-compose up --build
```

This will build and start all three containers:
- `hardware-server`: The virtual hardware server
- `ollama`: The Ollama LLM server
- `hardware-client`: The client that connects to both servers

### 2. Interact with the System

Once the containers are running, you can interact with the system through the `hardware-client` container. The client provides a command-line interface where you can type natural language commands to control the virtual hardware.

Example commands:
- "Turn on the LED on pin 17"
- "Blink the LED on pin 18"
- "Take a picture with the camera"
- "Record audio for 5 seconds"
- "Play the text 'Hello, world!' as audio"

### 3. Stop the Containers

To stop the containers, press `Ctrl+C` in the terminal where you started Docker Compose, or run:

```bash
docker-compose down
```

## Configuration

### Environment Variables

You can configure the system using environment variables in the `docker-compose.yml` file:

#### Hardware Server
- `HOST`: The hostname to bind the server to (default: `0.0.0.0`)
- `PORT`: The port to listen on (default: `8080`)
- `SERVER_NAME`: The name of the MCP server (default: `Virtual Hardware Server`)

#### Client
- `HARDWARE_SERVER_HOST`: The hostname of the hardware server (default: `hardware-server`)
- `HARDWARE_SERVER_PORT`: The port of the hardware server (default: `8080`)
- `OLLAMA_HOST`: The hostname of the Ollama server (default: `ollama`)
- `OLLAMA_PORT`: The port of the Ollama server (default: `11434`)
- `OLLAMA_MODEL`: The LLM model to use (default: `llama2`)

## Available Virtual Hardware

The virtual hardware server simulates the following hardware devices:

### GPIO
- Virtual LEDs that can be turned on, off, or blinked
- Virtual buttons that can be pressed and released
- General GPIO pins that can be set up as input or output

### Camera
- Virtual camera that simulates image capture
- Face detection simulation
- Motion detection simulation

### Audio
- Virtual microphone for audio recording
- Virtual speaker for audio playback
- Text-to-speech simulation

### Input
- Virtual keyboard for typing text
- Virtual mouse for cursor control

## Extending the System

### Adding New Virtual Hardware

To add new virtual hardware devices, modify the `hardware_server.py` file in the `docker/server` directory. You can add new tools to the LLM server by implementing them in the `_register_custom_tools` method of the `VirtualHardwareServer` class.

### Using Different LLM Models

The system uses Ollama as the LLM provider, which supports various models. You can change the model by setting the `OLLAMA_MODEL` environment variable in the `docker-compose.yml` file. The default model is `llama2`.

## Troubleshooting

### Connection Issues

If the client cannot connect to the hardware server or the Ollama server, check the following:
- Ensure all containers are running (`docker-compose ps`)
- Check the logs for error messages (`docker-compose logs`)
- Verify the network configuration in `docker-compose.yml`

### LLM Issues

If the LLM is not responding correctly:
- Check if the model is available (`docker exec -it ollama ollama list`)
- Try using a different model by setting the `OLLAMA_MODEL` environment variable
- Increase the timeout values in the client code if needed

## License

This project is licensed under the same license as the UnitMCP project.
