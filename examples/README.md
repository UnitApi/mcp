# UnitMCP Project Examples

This directory contains various examples demonstrating the capabilities of the UnitMCP Hardware Project.

## Directory Structure

- **basic/** - Basic examples for getting started with UnitMCP
- **platforms/** - Platform-specific examples (Raspberry Pi, PC, etc.)
- **llm/** - Large Language Model integration examples (Claude, Ollama)
- **advanced/** - Advanced usage patterns and complex demonstrations
- **shell_cli/** - Shell CLI interface examples for remote device control
- **audio/** - Audio recording, playback, and processing examples
- **automation/** - Automation scripts, pipelines, and workflow examples
- **dsl/** - Domain-Specific Language for hardware configuration and natural language control
- **hardware_demos/** - Hardware integration demonstrations (LEDs, sensors, actuators)
- **input_devices/** - Keyboard and mouse automation examples
- **integrated_demo/** - Complex demos integrating multiple features
- **rpi_control/** - Raspberry Pi GPIO and hardware control demonstrations
- **security/** - Security systems and monitoring examples
- **server/** - Server startup and configuration examples
- **tts/** - Text-to-speech examples
- **voice_assistant/** - Voice control and voice assistant implementations

Each subdirectory contains its own README with specific instructions and explanations.

## Environment Configuration

UnitMCP examples can be configured using environment variables, which provide a flexible way to customize behavior without changing code. There are three main ways to configure the environment:

### 1. Using .env Files

The `.env` file is a simple text file containing key-value pairs that define environment variables. Each example directory includes an `.env.example` file that you can copy and customize:

```bash
# Copy the example file to create your own .env file
cp .env.example .env

# Edit the .env file with your preferred settings
nano .env
```

When you run any UnitMCP example, it will automatically load the variables from the `.env` file in the current directory.

#### How .env Files Work

1. The `.env` file is loaded at the start of execution
2. Variables defined in the file are made available to the application
3. These variables override default values but can be overridden by command-line arguments
4. Comments in the file start with `#` and are ignored

#### Example .env File (Simulation Mode)

```
# Server configuration
SERVER_HOST=localhost
SERVER_PORT=8080
LOG_LEVEL=INFO

# Hardware configuration
SIMULATION=1
GPIO_PINS=17,18,27
LED_PINS=17,22
```

#### Example .env File (Real Hardware)

```
# Server configuration
SERVER_HOST=192.168.1.2  # IP address of your Raspberry Pi
SERVER_PORT=8080
LOG_LEVEL=INFO

# Hardware configuration
SIMULATION=0
GPIO_PINS=17,18,27
LED_PINS=18
```

### 2. Using Command-Line Environment Variables

You can also set environment variables directly when running a command:

```bash
# Run with simulation enabled
SIMULATION=1 python runner.py

# Connect to a specific Raspberry Pi
SERVER_HOST=192.168.1.2 SERVER_PORT=8888 python runner.py
```

This method overrides any values set in the `.env` file.

### 3. Using YAML Configuration Files

For more complex configurations, UnitMCP supports YAML files. Each example includes default configuration files in the `config/` directory:

```bash
# Run with a custom server configuration
python runner.py --server-config config/custom_server.yaml
```

#### Example YAML Configuration (Server)

```yaml
# server.yaml
server:
  host: 0.0.0.0
  port: 8080
  log_level: INFO
  
hardware:
  simulation: true
  gpio_pins: [17, 18, 27]
  led_pins: [17, 22]
```

#### Example YAML Configuration (Client)

```yaml
# client.yaml
client:
  host: 192.168.1.2
  port: 8080
  timeout: 30
  
commands:
  aliases:
    led_on: "gpio 18 out 1"
    led_off: "gpio 18 out 0"
```

### Configuration Precedence

When multiple configuration methods are used, the precedence order is:

1. Command-line environment variables (highest priority)
2. `.env` file variables
3. YAML configuration files
4. Default values in code (lowest priority)

## Simulation vs. Real Hardware

UnitMCP allows you to easily switch between simulation mode and real hardware:

### Simulation Mode

Simulation mode allows you to test your code without physical hardware. Enable it by setting `SIMULATION=1`:

```bash
# Via .env file
echo "SIMULATION=1" >> .env

# Via command line
SIMULATION=1 python runner.py
```

In simulation mode:
- GPIO operations are simulated in memory
- Hardware interactions are logged but not actually performed
- You can test your code on any computer without physical hardware

### Real Hardware Mode

To control real hardware (like a Raspberry Pi), disable simulation by setting `SIMULATION=0`:

```bash
# Via .env file
echo "SIMULATION=0" >> .env

# Via command line
SIMULATION=0 python runner.py
```

When using real hardware:
- Make sure to set the correct `SERVER_HOST` to your device's IP address
- Ensure you have the proper permissions to access GPIO pins
- Connect the physical hardware according to your pin configuration

### Example: Controlling an LED

#### Simulation Mode

```bash
# .env file
SERVER_HOST=localhost
SERVER_PORT=8080
SIMULATION=1
LED_PINS=18

# Command
python examples/shell_cli/runner.py
```

Output:
```
[INFO] Running in simulation mode
[INFO] LED on pin 18 turned ON (simulated)
[INFO] LED on pin 18 turned OFF (simulated)
```

#### Real Hardware Mode

```bash
# .env file
SERVER_HOST=192.168.1.2
SERVER_PORT=8080
SIMULATION=0
LED_PINS=18

# Command
python examples/shell_cli/runner.py
```

Output:
```
[INFO] Connected to hardware at 192.168.1.2:8080
[INFO] LED on pin 18 turned ON
[INFO] LED on pin 18 turned OFF
```

## Remote Device Control with Shell CLI

The `shell_cli` directory contains examples for connecting to and controlling remote devices interactively:

- **shell_cli_demo.py** - Demonstrates how to use the interactive shell to control hardware
- **simple_remote_shell.py** - Simplified shell implementation for remote device control without requiring the full UnitMCP installation
- **client.py** - Client implementation for connecting to remote devices
- **server.py** - Server implementation for exposing device capabilities

### Starting a Remote Server

To set up a remote server for GPIO control:

```bash
# On the device with GPIO pins (e.g., Raspberry Pi)
cd examples/shell_cli
python server.py --config config/server.yaml
```

The server will listen for connections and expose GPIO control capabilities to remote clients.

### Connecting to the Remote Server

Once the server is running, you can connect to it using either the full UnitMCP shell or the simple remote shell:

```bash
# Using the full UnitMCP shell
cd examples/shell_cli
python shell_cli_demo.py --interactive

# In the shell
mcp> connect 192.168.1.100 8888
mcp> status                      # Check connection status
mcp> gpio_setup 17 OUT           # Set up GPIO pin
mcp> led_setup led1 17           # Configure LED on pin 17
mcp> led led1 on                 # Turn on the LED
```

For SSH connections to a Raspberry Pi, you need to specify the username:

```bash
# Connect via SSH to Raspberry Pi
cd examples/shell_cli
python simple_remote_shell.py --host 192.168.1.2 --port 22 --ssh --username pi

# Or set in .env file
# RPI_USERNAME=pi
# python simple_remote_shell.py --host 192.168.1.2 --port 22 --ssh
```

### Interactive Remote Device Control

For interactive control of remote devices, you can use either:

1. **Full UnitMCP Shell** (`shell_cli_demo.py`) - Provides complete access to all UnitMCP features
2. **Simple Remote Shell** (`simple_remote_shell.py`) - Lightweight alternative using standard Python libraries

The simple remote shell supports both SSH and TCP connections:

```bash
# Connect via TCP
python simple_remote_shell.py --host 192.168.1.100 --port 8888

# Connect via SSH (requires paramiko)
python simple_remote_shell.py --host 192.168.1.100 --port 22 --ssh
```

### Controlling GPIO Pins Remotely

Once connected with the simple remote shell, you can control GPIO pins with these commands:

```
# Set up a GPIO pin as output
(remote) gpio 17 out 1

# Set up a GPIO pin as input
(remote) gpio 18 in

# Read a GPIO pin value
(remote) gpio 17 read

# Control an LED connected to a GPIO pin
(remote) led led1 setup 17
(remote) led led1 on
(remote) led led1 off
(remote) led led1 blink 0.5 0.5
```

## GPIO Streaming from Raspberry Pi

The `rpi_control` directory contains examples for streaming GPIO data from a Raspberry Pi to a client PC:

- **gpio_example.py** - Basic GPIO control with streaming updates
- **client.py** - Client implementation for receiving GPIO updates
- **server.py** - Server implementation for sending GPIO updates

To stream GPIO data from a Raspberry Pi to a client PC:

1. On the Raspberry Pi, start the server:
   ```bash
   cd examples/rpi_control
   python server.py
   ```

2. On the client PC, run the client:
   ```bash
   cd examples/rpi_control
   python client.py --host <raspberry_pi_ip>
   ```

3. Use the GPIO example to monitor real-time changes:
   ```bash
   cd examples/rpi_control
   python gpio_example.py --host <raspberry_pi_ip>
   ```

The GPIO streaming examples work by:
1. Setting up a WebSocket connection between the client and server
2. The server monitors GPIO pin state changes in real-time
3. When a change is detected, it's immediately sent to connected clients
4. Clients can also send commands to control GPIO pins

This approach provides real-time, bidirectional communication between the Raspberry Pi and client PC, making it ideal for remote monitoring and control applications.

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
| `SIMULATION` | Run in simulation mode without hardware | 0 |
| `VERBOSE` | Enable verbose logging | 0 |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO |
| `ENABLE_CLAUDE_PLUGIN` | Enable the Claude UnitMCP Plugin | 0 |

## Configuration Files

All configuration files have been moved to the `/configs` directory:

- Environment variables: `/configs/env/`
- YAML configurations: `/configs/yaml/`

To load configuration files in your code, use the following paths:

```python
# Load environment variables
from dotenv import load_dotenv
import os

# Load from the new location
load_dotenv("/path/to/configs/env/default.env")

# Load YAML configuration
import yaml

# Load from the new location
with open("/path/to/configs/yaml/devices/default.yaml", "r") as f:
    config = yaml.safe_load(f)
```

See the [Migration Guide](/docs/MIGRATION_GUIDE.md) for more details on the new structure.

## Quick Start

To run any example, navigate to its directory and execute the Python script:

```bash
cd examples/dsl
SIMULATION=1 python quickstart_demo.py
```

### New Quickstart Demo (May 2025)

We've added a new quickstart demo that showcases the latest features:

- **DSL Configuration**: Load and control devices using YAML configurations
- **Natural Language Control**: Process natural language commands with Claude 3.7
- **CLI Command Parsing**: Parse and execute CLI commands
- **Simulation Mode**: Run without requiring physical hardware

To run the quickstart demo:

```bash
cd examples/dsl
SIMULATION=1 VERBOSE=1 python quickstart_demo.py
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

## Testing Examples

To test all examples in simulation mode, you can use the provided test script:

```bash
# Install required dependencies
pip install -e .
pip install pyyaml

# Run all examples in simulation mode
python test_examples.py
```

This will run each example with a timeout and report any failures. You can also test specific examples:

```bash
# Test a specific example
cd examples/shell_cli
SIMULATION=1 python shell_cli_demo.py
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
5. **Module Not Found**: Make sure to install the project with `pip install -e .`

## Creating Your Own Examples

Use these examples as templates for your own automation:

1. Copy a similar example
2. Modify the hardware setup
3. Adjust the control logic
4. Add error handling as needed
5. Use environment variables for configuration

For more information, see the main project documentation.
