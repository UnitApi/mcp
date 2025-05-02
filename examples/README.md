# MCP Hardware Project Examples

This directory contains various examples demonstrating the capabilities of the MCP Hardware Project.

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

## Quick Start

To run any example, navigate to its directory and execute the Python script:

```bash
python examples/hardware_demos/led_control.py
python examples/automation/pipeline_demo.py
python examples/server/start_server.py
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

## Common Issues

1. **Permission Errors**: Run with appropriate permissions for hardware access
2. **Missing Hardware**: Some examples will simulate if hardware is not present
3. **Server Connection**: Ensure the MCP server is running before examples

## Creating Your Own Examples

Use these examples as templates for your own automation:

1. Copy a similar example
2. Modify the hardware setup
3. Adjust the control logic
4. Add error handling as needed

For more information, see the main project documentation.
