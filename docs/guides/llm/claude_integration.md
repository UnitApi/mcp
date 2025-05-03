# Claude Integration Guide

This guide explains how to use the Claude UnitMCP Plugin for advanced natural language hardware control.

## Overview

The Claude UnitMCP Plugin enables sophisticated natural language understanding for controlling hardware devices through the UnitMCP framework. It supports multi-turn conversations, context-aware command processing, and robust error handling with conversational recovery strategies.

## Installation

The Claude UnitMCP Plugin is included in the UnitMCP package. To use it, you need to have UnitMCP installed:

```bash
pip install unitmcp
```

## Key Features

- **Advanced NLP**: Parse complex natural language commands into structured hardware commands
- **Conversation State Management**: Maintain context across multi-turn interactions
- **DSL Integration**: Leverage the UnitMCP DSL system for configuration and command execution
- **Simulation Mode**: Test hardware control in a simulated environment
- **Error Handling**: Provide user-friendly error messages and recovery suggestions

## Usage

### Basic Usage

```python
import asyncio
from unitmcp.plugin.main import ClaudeUnitMCPPlugin

async def main():
    # Initialize the plugin
    plugin = ClaudeUnitMCPPlugin()
    await plugin.initialize()
    
    # Process a natural language query
    query = {
        "text": "Turn on the LED",
        "conversation_id": "my_conversation",
        "user_id": "user123"
    }
    
    response = await plugin.process_query(query)
    
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multi-turn Conversation

```python
import asyncio
from unitmcp.plugin.main import ClaudeUnitMCPPlugin

async def main():
    # Initialize the plugin
    plugin = ClaudeUnitMCPPlugin()
    await plugin.initialize()
    
    # First query
    query1 = {
        "text": "Turn on the kitchen light",
        "conversation_id": "my_conversation",
        "user_id": "user123"
    }
    
    response1 = await plugin.process_query(query1)
    print(response1)
    
    # Second query (referring to the first)
    query2 = {
        "text": "Set it to 50% brightness",
        "conversation_id": "my_conversation",
        "user_id": "user123"
    }
    
    response2 = await plugin.process_query(query2)
    print(response2)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The Claude UnitMCP Plugin can be configured using environment variables or a configuration file:

### Environment Variables

- `ENABLE_CLAUDE_PLUGIN`: Enable the Claude UnitMCP Plugin (default: `0`)
- `SIMULATION`: Run in simulation mode without hardware (default: `0`)
- `VERBOSE`: Enable verbose logging (default: `0`)

### Configuration File

You can also configure the plugin using a JSON configuration file:

```json
{
    "host": "localhost",
    "port": 8888,
    "simulation_mode": true,
    "verbose": true
}
```

Load the configuration file when initializing the plugin:

```python
plugin = ClaudeUnitMCPPlugin(config_path="path/to/config.json")
```

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

## Troubleshooting

If you encounter issues with the Claude UnitMCP Plugin, check the following:

1. Ensure the plugin is enabled: `ENABLE_CLAUDE_PLUGIN=1`
2. Check the logs for error messages: `VERBOSE=1`
3. Try running in simulation mode: `SIMULATION=1`
4. Verify that your hardware devices are properly configured

For more help, see the [Troubleshooting Guide](../troubleshooting/README.md).
