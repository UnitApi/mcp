# UnitMCP Project Examples

This directory contains various examples demonstrating the capabilities of the UnitMCP Hardware Project.

## Directory Structure

- **audio/** - Audio recording, playback, and processing examples
- **automation/** - Automation scripts, pipelines, and workflow examples
- **hardware_demos/** - Hardware integration demonstrations (LEDs, sensors, actuators)
- **input_devices/** - Keyboard and mouse automation examples
- **integrated_demo/** - Complex demos integrating multiple features
- **ollama_integration/** - Examples showing integration with Ollama LLM
- **rpi_control/** - Raspberry Pi GPIO and hardware control demonstrations
- **security/** - Security systems and monitoring examples
- **server/** - Server startup and configuration examples
- **shell_cli/** - Shell CLI interface examples
- **tts/** - Text-to-speech examples
- **voice_assistant/** - Voice control and voice assistant implementations

Each subdirectory contains its own README with specific instructions and explanations.

## Environment Variables

All examples in this project now support configuration via environment variables. This approach provides several benefits:

1. **Consistent Configuration**: Use the same configuration method across all examples
2. **Secure Credentials**: Keep sensitive information out of your code
3. **Flexible Deployment**: Easily adapt to different environments without code changes
4. **Simplified Testing**: Switch between real hardware and simulation mode

### Using Environment Variables

You can set environment variables in three ways:

1. **Create a `.env` file**: Each example directory contains a `txt.env` template that you can copy to `.env`
2. **Set in your shell**: Export variables before running examples (`export RPI_HOST=192.168.1.100`)
3. **Pass via command line**: Set variables when running examples (`RPI_HOST=192.168.1.100 python example.py`)

### Common Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RPI_HOST` | Hostname or IP address of the MCP server | localhost |
| `RPI_PORT` | Port number of the MCP server | 8080 |
| `SIMULATION_MODE` | Run in simulation mode without hardware | false |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO |

## Quick Start

To run any example, navigate to its directory and execute the Python script:

```bash
# Run with default settings (uses .env file if present)
python examples/hardware_demos/led_control.py

# Run with specific environment variables
RPI_HOST=192.168.1.100 python examples/hardware_demos/led_control.py

# Run with custom environment file
python examples/automation/pipeline_demo.py --env-file custom.env
```

Make sure you have installed the required dependencies:
```bash
pip install -e .
pip install -e ".[ollama]"  # For Ollama integration examples
```

## Running Examples

Most examples have multiple demos. When you run them, you'll see a menu:

```bash
$ python examples/hardware_demos/led_control.py
LED Control Demo
1. Simple blink
2. LED patterns
Select demo (1-2): 
```

## Hardware Requirements

Different examples require different hardware:

- **GPIO Examples**: Raspberry Pi with LEDs, buttons, sensors
- **Audio Examples**: Microphone and speakers
- **Camera Examples**: USB webcam or Pi Camera
- **Input Examples**: Any computer with keyboard/mouse

You can run most examples in simulation mode by setting `SIMULATION_MODE=true` in your environment variables.

## Common Issues

1. **Permission Errors**: Run with appropriate permissions for hardware access
2. **Missing Hardware**: Some examples will simulate if hardware is not present
3. **Server Connection**: Ensure the MCP server is running before examples
4. **Environment Variables**: Check that your `.env` file is in the correct directory

## Creating Your Own Examples

Use these examples as templates for your own automation:

1. Copy a similar example
2. Modify the hardware setup
3. Adjust the control logic
4. Add error handling as needed
5. Use environment variables for configuration

For more information, see the main project documentation.
