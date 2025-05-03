# UnitMCP Raspberry Pi Control Examples

This directory contains various examples for controlling Raspberry Pi hardware using the UnitMCP library. These examples demonstrate hardware control, automation, audio processing, and more.

## Hardware Control Examples

### hardware_client.py

Client application that connects to a UnitMCP server to control hardware remotely.

**Features:**
- Remote GPIO control
- LED management
- Button and sensor input
- Secure communication

### hardware_server.py

Server application that exposes hardware functionality to remote clients.

**Features:**
- GPIO server
- Permission management
- Multiple client support
- Hardware abstraction

### gpio_example.py

Direct GPIO control example showing pin manipulation.

**Features:**
- Pin setup and control
- Input and output operations
- Interrupt handling
- PWM control

## Audio Examples

### audio_example.py

Demonstrates audio playback and recording capabilities.

**Features:**
- Audio file playback
- Text-to-speech
- Audio recording
- Volume control

### lcd_example.py

Example showing how to control LCD displays.

**Features:**
- Text display
- Custom characters
- Scrolling text
- Status indicators

## Automation Examples

### config_automation_example.py

This example demonstrates how to use YAML configuration files to define automation rules, triggers, and actions without writing code.

**Features:**
- Configuration-based automation
- Time-based and GPIO-based triggers
- LED, audio, and logging actions
- Sequence definition and execution

### simple_config_demo.py

A simplified version of the configuration-based automation example with minimal setup.

**Features:**
- Basic time triggers
- Simple action sequences
- Minimal configuration

### automation_example.py

A code-based approach to automation that doesn't rely on configuration files.

**Features:**
- Programmatically defined triggers and actions
- Custom automation sequences
- Hardware control integration

## Discovery and Installation

### hardware_discovery_example.py

Example showing how to discover and enumerate available hardware.

**Features:**
- Automatic hardware detection
- Capability discovery
- Hardware information reporting

### installation_example.py

Example demonstrating how to install and configure UnitMCP components.

**Features:**
- Dependency management
- Configuration setup
- Service installation

## Configuration Files

The automation system uses YAML configuration files to define triggers, actions, and sequences:

- **automation_config.yaml**: Standard configuration example
- **env_automation_config.yaml**: Environment variable-aware configuration
- **my_custom_config.yaml**: Custom configuration with comprehensive examples of triggers and sequences

## Running the Examples

### Individual Examples

You can run each example individually:

```bash
# Run with default settings (uses .env file if present)
python hardware_client.py

# Run automation example with specific configuration file
python config_automation_example.py --config my_custom_config.yaml

# Run with specific environment variables
RPI_HOST=192.168.1.100 DEMO_DURATION=60 python config_automation_example.py

# Run with custom environment file
python config_automation_example.py --env-file custom.env

# Run the audio example with specific volume
AUDIO_VOLUME=0.5 python audio_example.py
```

### Running All Examples

To run all examples in sequence, use the provided script:

```bash
# Make the script executable (if needed)
chmod +x run_examples.sh

# Run all examples
./run_examples.sh
```

The script will:
- Run each example for a specified duration
- Display descriptions of what each example does
- Allow you to press Ctrl+C to skip to the next example
- Include colorized output for better readability

## Environment Variables

All examples in this directory support configuration via environment variables. You can:

1. Create a `.env` file in this directory (copy from `txt.env` as a starting point)
2. Set environment variables in your shell before running the examples
3. Pass configuration via command-line arguments (where supported)

### Common Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RPI_HOST` | Hostname or IP address of the MCP server | 127.0.0.1 |
| `RPI_PORT` | Port number of the MCP server | 8888 |
| `SIMULATION_MODE` | Run in simulation mode without hardware | true |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO |
| `LOG_FILE` | Path to the log file | automation.log |

### Hardware Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LED_PIN` | GPIO pin for the LED | 18 |
| `BUTTON_PIN` | GPIO pin for the button | 17 |
| `GPIO_ENABLED` | Enable GPIO functionality | true |
| `AUDIO_ENABLED` | Enable audio functionality | true |
| `CAMERA_ENABLED` | Enable camera functionality | false |

### Automation Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIG_FILE` | Path to the YAML configuration file | automation_config.yaml |
| `DEMO_DURATION` | Duration to run the demo in seconds | 30.0 |
| `TIME_TRIGGER_INTERVAL` | Interval for time-based triggers in seconds | 10.0 |
| `TIME_TRIGGER_MAX_COUNT` | Maximum number of times a time trigger will fire | 3 |
| `SEQUENCE_DELAY` | Default delay between sequence actions in seconds | 2.0 |

### Audio Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_FREQUENCY` | Frequency for tone generation in Hz | 440 |
| `AUDIO_DURATION` | Duration of audio playback in seconds | 0.5 |
| `TTS_MESSAGE` | Text to speak for text-to-speech actions | "Hello, UnitMCP automation system is running!" |
| `AUDIO_VOLUME` | Default audio volume (0.0-1.0) | 0.8 |

## Requirements

- UnitMCP library: `pip install -e ..`
- PyYAML: `pip install pyyaml` (for configuration-based examples)
- RPi.GPIO: `pip install RPi.GPIO` (when running on actual Raspberry Pi)
- Appropriate hardware or simulation mode enabled
