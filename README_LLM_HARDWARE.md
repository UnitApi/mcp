# LLM Hardware Control with UnitMCP

This project demonstrates how to use Large Language Models (LLMs) like Ollama to control hardware devices through the UnitMCP framework. It includes a Docker Compose setup for testing hardware control in a virtual environment.

## Overview

The integration allows you to:

1. Control hardware devices (GPIO, camera, audio, etc.) using natural language commands
2. Test hardware control in a virtual environment using Docker
3. Extend the system with custom hardware devices and LLM models

## Components

### UnitMCP Framework

The UnitMCP framework provides a unified interface for hardware control across different platforms. It includes:

- **Client**: Connects to the hardware server and sends control commands
- **Server**: Manages hardware devices and executes control commands
- **Protocols**: Defines the communication protocol between client and server
- **Hardware Modules**: Implements control for specific hardware types (GPIO, camera, audio, etc.)

### LLM Integration

The LLM integration allows natural language control of hardware devices:

- **LLM Server**: Processes natural language commands and converts them to hardware control commands
- **LLM Client**: Connects to both the LLM server and the hardware server
- **Tools**: Exposes hardware control capabilities to the LLM

### Docker Environment

The Docker environment provides a virtual testing ground for hardware control:

- **Virtual Hardware Server**: Simulates hardware devices in a containerized environment
- **Ollama Container**: Runs the LLM for natural language processing
- **Client Container**: Provides a user interface for interacting with the system

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your system
- Basic knowledge of Python and Docker
- Understanding of the UnitMCP hardware control system

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/unitmcp.git
cd unitmcp
```

2. Build and start the Docker containers:

```bash
docker-compose up --build
```

### Usage

Once the containers are running, you can interact with the system through the client container. The client provides a command-line interface where you can type natural language commands to control the virtual hardware.

Example commands:

- "Turn on the LED on pin 17"
- "Blink the LED on pin 18"
- "Take a picture with the camera"
- "Record audio for 5 seconds"
- "Play the text 'Hello, world!' as audio"

## Project Structure

```
unitmcp/
├── docker/                 # Docker setup for virtual testing
│   ├── client/             # Client container files
│   │   ├── Dockerfile      # Client container definition
│   │   └── llm_client.py   # LLM client implementation
│   ├── server/             # Server container files
│   │   ├── Dockerfile      # Server container definition
│   │   └── hardware_server.py # Virtual hardware server implementation
│   └── README.md           # Docker setup documentation
├── src/                    # Source code for the UnitMCP framework
│   └── unitmcp/            # Main package
│       ├── client/         # Client implementation
│       ├── server/         # Server implementation
│       ├── protocols/      # Protocol definitions
│       └── utils/          # Utilities
├── rpi_control/            # Raspberry Pi specific code
│   └── examples/           # Example scripts for hardware control
├── docker-compose.yml      # Docker Compose configuration
└── README_LLM_HARDWARE.md  # This file
```

## Docker Setup

The Docker setup includes three containers:

1. **hardware-server**: Runs the virtual hardware server that simulates hardware devices
2. **ollama**: Runs the Ollama LLM server for natural language processing
3. **hardware-client**: Runs the client that connects to both servers

For more details on the Docker setup, see the [Docker README](docker/README.md).

## Real Hardware Setup

To use this system with real hardware (e.g., Raspberry Pi):

1. Install the UnitMCP framework on your hardware device:

```bash
pip install unitmcp
```

2. Start the hardware server on your device:

```bash
python -m unitmcp.server.start
```

3. Configure the client to connect to your hardware device:

```bash
export HARDWARE_SERVER_HOST=your_device_ip
export HARDWARE_SERVER_PORT=8080
python -m unitmcp.client.llm_client
```

## Extending the System

### Adding New Hardware Devices

To add support for new hardware devices:

1. Create a new server module in `src/unitmcp/server/`
2. Implement the necessary control methods
3. Register the server with the main hardware server
4. Add tools to the LLM server to expose the new capabilities

### Using Different LLM Models

The system uses Ollama as the LLM provider, which supports various models. You can change the model by setting the `OLLAMA_MODEL` environment variable in the `docker-compose.yml` file. The default model is `llama2`.

## Examples

### Basic LED Control

```python
from unitmcp.client import MCPHardwareClient

async def control_led():
    async with MCPHardwareClient() as client:
        # Set up LED on pin 17
        await client.setup_pin(17, "output")
        
        # Turn on LED
        await client.write_pin(17, 1)
        
        # Wait for 1 second
        await asyncio.sleep(1)
        
        # Turn off LED
        await client.write_pin(17, 0)

asyncio.run(control_led())
```

### Natural Language Control

```
You: Turn on the LED on pin 17
Assistant: I'll turn on the LED on pin 17 for you.

{
  "tool": "virtual_led_control",
  "arguments": {
    "pin": 17,
    "state": "on"
  }
}

Tool execution result: {'success': True, 'message': 'Virtual LED on pin 17 turned on'}
```

## Troubleshooting

### Connection Issues

If the client cannot connect to the hardware server or the LLM server, check the following:
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

## Acknowledgments

- Anthropic MCP team for the protocol
- Raspberry Pi Foundation for hardware libraries
- Open source community for contributions
