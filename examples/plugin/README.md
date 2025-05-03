# Claude UnitMCP Plugin

This directory contains examples demonstrating the Claude UnitMCP Plugin, which provides advanced natural language processing capabilities for hardware control.

## Overview

The Claude UnitMCP Plugin enables sophisticated natural language understanding for controlling hardware devices through the UnitMCP framework. It supports multi-turn conversations, context-aware command processing, and robust error handling with conversational recovery strategies.

## Key Features

- **Advanced NLP**: Parse complex natural language commands into structured hardware commands
- **Conversation State Management**: Maintain context across multi-turn interactions
- **DSL Integration**: Leverage the UnitMCP DSL system for configuration and command execution
- **Simulation Mode**: Test hardware control in a simulated environment
- **Error Handling**: Provide user-friendly error messages and recovery suggestions

## Examples

### Quickstart Demo

The 
- Natural language command processing
- Hardware control in simulation mode
- Multi-turn conversation support
- Error handling and recovery

To run the quickstart demo:

```bash
# Run in simulation mode with verbose logging
SIMULATION=1 VERBOSE=1 python quickstart_demo.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SIMULATION` | Run in simulation mode without hardware | 1 |
| `VERBOSE` | Enable verbose logging | 0 |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO |

## Sample Commands

The Claude UnitMCP Plugin supports a wide range of natural language commands, including:

- "Turn on the LED"
- "Make the traffic light show green"
- "Show 'Hello World' on the display"
- "Turn off the LED"
- "Blink the LED at 2 Hz"
- "Press the button"
- "Make the traffic light cycle through all colors"

More complex commands with multiple actions and parameters are also supported:

- "Turn on the kitchen light and set it to 50% brightness"
- "Create a traffic light sequence that cycles every 5 seconds"
- "Show the temperature on the display and update it every minute"

## Integration with Other UnitMCP Components

The Claude UnitMCP Plugin integrates with several other UnitMCP components:

- **DSL System**: For configuration loading and command execution
- **MockDeviceFactory**: For testing in simulation mode
- **MCPHardwareClient**: For hardware command execution
- **Error Handling**: For robust error handling and recovery

## Next Steps

For more advanced usage and integration with your own projects, see the following resources:

- UnitMCP Implementation Guide
- DSL Configuration Guide
- Hardware Integration Guide
