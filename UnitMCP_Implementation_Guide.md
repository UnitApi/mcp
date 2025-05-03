# UnitMCP Implementation Guide

## Overview

UnitMCP is a hardware control framework designed for Raspberry Pi and similar devices. It provides a Domain-Specific Language (DSL) for configuring and controlling hardware devices, as well as natural language processing capabilities through Claude 3.7 integration.

This guide documents the implementation, testing, and usage of the UnitMCP system.

## Key Components

### 1. DSL System

The DSL system allows users to define hardware configurations in YAML format and control devices using a simple command structure.

Key components:
- **DslCompiler**: Compiles DSL configurations and detects format
- **YAML Parser**: Parses YAML configurations into Python dictionaries
- **DeviceConverter**: Converts DSL device configurations into UnitMCP device objects

### 2. Hardware Integration

The hardware integration layer connects the DSL system to physical hardware devices.

Key components:
- **DslHardwareIntegration**: Loads configurations, initializes devices, and executes commands
- **DeviceFactory**: Creates hardware device objects based on configuration
- **MockDeviceFactory**: Provides simulation capabilities for testing without hardware

### 3. Natural Language Processing

The NLP system allows users to control hardware using natural language commands.

Key components:
- **ClaudeIntegration**: Processes natural language commands using Claude 3.7
- **Command Extraction**: Extracts device commands from natural language

### 4. Command Line Interface

The CLI provides a simple interface for controlling devices and processing natural language commands.

Key components:
- **CommandParser**: Parses CLI commands for device control and natural language processing

## Implementation Details

### Simulation Mode

UnitMCP can run in simulation mode without requiring actual hardware. This is useful for development and testing.

To enable simulation mode:
```bash
export SIMULATION=1
```

### Mock Device Factory

The `MockDeviceFactory` provides mock implementations of hardware devices for testing. It simulates device behavior without requiring actual hardware.

Key features:
- Creates mock devices of various types (LED, button, display, etc.)
- Simulates device initialization, control, and cleanup
- Logs device actions for verification

### Device Converter

The `DeviceConverter` converts DSL device configurations into UnitMCP device objects. It uses the `DeviceFactory` to create the actual device objects.

In simulation mode, it uses the `MockDeviceFactory` to create mock devices.

### Claude Integration

The Claude integration processes natural language commands using Claude 3.7. It converts natural language into structured device commands.

## Testing

### Integration Tests

The integration tests verify that all components work together correctly. They test:
- DSL compilation and parsing
- Device conversion
- Hardware integration
- Natural language processing
- CLI command parsing

### Detailed Tests

The detailed tests focus on specific components and verify their functionality in isolation.

### Running Tests

To run the tests:
```bash
cd /home/tom/github/UnitApi/mcp
SIMULATION=1 VERBOSE=1 python test_unitmcp_integration.py
```

## Usage Examples

### Basic DSL Configuration

```yaml
devices:
  led1:
    type: led
    pin: 17
    name: Status LED
  button1:
    type: button
    pin: 18
    name: Control Button
```

### Loading Configuration

```python
from unitmcp.dsl.integration import DslHardwareIntegration

# Create the DSL hardware integration
integration = DslHardwareIntegration()

# Load the configuration
await integration.load_config(config_yaml)

# Initialize the devices
await integration.initialize_devices()
```

### Executing Commands

```python
# Turn on an LED
command = {"device": "led1", "action": "on", "parameters": {}}
result = await integration.execute_command(command)

# Blink an LED
command = {"device": "led1", "action": "blink", "parameters": {"duration": 2, "count": 3}}
result = await integration.execute_command(command)
```

### Natural Language Commands

```python
from unitmcp.llm.claude import ClaudeIntegration

# Create the Claude integration
claude = ClaudeIntegration(api_key="your_api_key")

# Process a natural language command
command = "Turn on the kitchen light"
processed_cmd = await claude.process_command(command)

# Execute the command
device_cmd = {
    "device": processed_cmd.get('target'),
    "action": processed_cmd.get('action'),
    "parameters": processed_cmd.get('parameters', {})
}
result = await integration.execute_command(device_cmd)
```

### CLI Commands

```bash
# Device control
mcp device led1 on

# Natural language
mcp natural turn on the kitchen light
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all required packages are installed.
2. **Hardware Connection**: Verify that hardware devices are properly connected.
3. **Simulation Mode**: Set `SIMULATION=1` to run without hardware.

### Logging

Enable verbose logging for detailed information:
```bash
export VERBOSE=1
```

## Next Steps

1. **Improve Error Handling**: Add more robust error handling for edge cases.
2. **Enhance Claude Integration**: Implement more sophisticated natural language processing.
3. **Add More Device Types**: Expand the device factory to support additional hardware components.
4. **Create Comprehensive Documentation**: Document all available commands and configuration options.
5. **Develop Unit Tests**: Create a comprehensive suite of unit tests for all components.

## Conclusion

UnitMCP provides a powerful framework for controlling hardware devices using both a domain-specific language and natural language commands. With the fixes and enhancements implemented, it now works reliably in both hardware and simulation modes.
