# UnitMCP DSL Integration

This directory contains examples and documentation for the UnitMCP Domain-Specific Language (DSL) integration.

## Overview

The UnitMCP DSL provides a simple and powerful way to configure and control hardware devices using:
- YAML configuration files
- Natural language commands via Claude 3.7
- Command-line interface

## Key Components

### DSL Compiler
The DSL compiler processes configuration files and converts them into a format that can be used by the UnitMCP system.

### Device Converter
The device converter transforms DSL device configurations into actual UnitMCP device objects.

### Hardware Integration
The hardware integration layer connects the DSL system to physical hardware devices.

### Claude 3.7 Integration
The Claude integration processes natural language commands and converts them to UnitMCP device commands.

### CLI Command Parser
The command parser processes command-line instructions for both device control and natural language processing.

## Examples

### Quickstart Demo
The 
```bash
# Run in simulation mode with verbose logging
SIMULATION=1 VERBOSE=1 python quickstart_demo.py
```

This demo showcases:
- Loading device configurations from YAML
- Initializing and controlling devices
- Processing natural language commands
- Parsing CLI commands

### DSL Example
The `dsl_example.py` script shows how to use the DSL to load device configurations and control hardware:

```bash
# Run in simulation mode
SIMULATION=1 python dsl_example.py
```

## Configuration

### Device Configuration
Devices are configured using YAML files. Here's an example configuration:

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

### Command Format
Commands follow a simple JSON structure:

```json
{
  "device": "led1",
  "action": "on",
  "parameters": {}
}
```

## Testing Results

### Latest Test Results (May 3, 2025)

All tests are now passing successfully after implementing the following fixes:

1. **DSL Compiler**: Added the `detect_format` method to properly identify the format of input configurations.

2. **Device Converter**: 
   - Created a concrete implementation using a mock device factory for testing
   - Fixed the device conversion process to handle simulation mode properly

3. **DSL Hardware Integration**:
   - Added support for simulation mode
   - Improved error handling for device creation
   - Added proper integration with the mock device factory

4. **Claude 3.7 Integration**:
   - Added missing imports (requests)
   - Implemented proper async handling for command processing

5. **CLI Command Parser**:
   - Added a `parse` method as an alias for `parse_shell_command`
   - Improved error handling for command parsing

### Test Coverage

The following components have been tested and verified:

- **YAML Configuration Parsing**: Successfully parses YAML configurations into Python dictionaries.
- **DSL Compilation**: Properly compiles DSL configurations and detects the format.
- **Device Conversion**: Converts DSL device configurations into UnitMCP device objects.
- **Hardware Integration**: Successfully loads configurations, initializes devices, and executes commands.
- **Claude 3.7 Integration**: Processes natural language commands and converts them to UnitMCP commands.
- **CLI Command Parsing**: Parses and executes CLI commands for device control and natural language processing.

### Running in Simulation Mode

To run the UnitMCP system in simulation mode without requiring actual hardware:

```bash
# Set the simulation environment variable
export SIMULATION=1

# For verbose logging
export VERBOSE=1

# Run your script
python your_script.py
```

This allows you to test and develop UnitMCP applications without needing physical Raspberry Pi hardware.

## Further Reading

For more detailed information, see the [UnitMCP Implementation Guide](../../UnitMCP_Implementation_Guide.md).
