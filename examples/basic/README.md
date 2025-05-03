# UnitMCP Basic Examples

This directory contains basic examples to help you get started with the UnitMCP hardware control framework. These examples demonstrate fundamental concepts and provide a foundation for more advanced applications.

## Available Examples

### DSL Quickstart Demo

The `dsl_quickstart_demo.py` demonstrates how to use the Domain-Specific Language (DSL) for hardware configuration and control:

```bash
# Run the DSL quickstart demo
python dsl_quickstart_demo.py

# Run in simulation mode
SIMULATION=1 python dsl_quickstart_demo.py
```

This example shows how to:
- Define hardware configurations using YAML
- Load and parse configuration files
- Set up hardware devices from configuration
- Control devices using the UnitMCP API
- Handle errors and provide useful feedback

## Files in This Directory

- `dsl_quickstart_demo.py` - Demo for using the DSL for hardware configuration
- `client.py` - Client implementation for connecting to the server
- `server.py` - Server implementation for handling client requests
- `runner.py` - Unified runner script to manage both client and server components
- `config/` - Directory containing configuration files:
  - `client.yaml` - Client configuration settings
  - `server.yaml` - Server configuration settings

## Using the Runner

The `runner.py` script provides a standardized way to start and manage both client and server components:

```bash
# Run both client and server with default configuration
python runner.py

# Run only the server
python runner.py --server-only

# Run only the client
python runner.py --client-only

# Specify custom configuration files
python runner.py --server-config config/custom_server.yaml --client-config config/custom_client.yaml

# Enable verbose logging
python runner.py --verbose
```

### Environment Configuration

The runner and example scripts can be configured using:

1. **Environment Variables (.env file)**: Create a `.env` file in the example directory with configuration values:

```
# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
LOG_LEVEL=INFO

# Hardware configuration
SIMULATION=1
GPIO_PINS=17,18,27
```

2. **Command Line Arguments**: Pass configuration values directly to the runner:

```bash
# Configure server host and port
SERVER_HOST=192.168.1.100 SERVER_PORT=8888 python runner.py

# Enable simulation mode
SIMULATION=1 python runner.py
```

3. **Configuration Files**: Specify custom YAML configuration files:

```bash
python runner.py --server-config config/custom_server.yaml
```

The configuration precedence is: Command Line > .env File > Default Configuration Files

## Core Concepts

These examples introduce several core UnitMCP concepts:

### 1. Hardware Abstraction

UnitMCP provides a hardware abstraction layer that allows you to work with devices in a consistent way:

```python
# Example hardware abstraction
from unitmcp.hardware import DeviceManager

# Create a device manager
device_manager = DeviceManager()

# Add a device
device_manager.add_device("led1", {
    "type": "led",
    "pin": 17,
    "active_high": True
})

# Control the device
device_manager.control_device("led1", "on")
```

### 2. Client-Server Architecture

UnitMCP uses a client-server architecture for remote hardware control:

```python
# Server-side code
from unitmcp.server import MCPServer

server = MCPServer(host="0.0.0.0", port=8080)
server.start()

# Client-side code
from unitmcp.client import MCPClient

client = MCPClient(host="localhost", port=8080)
client.connect()
client.send_command("gpio_setup", {"pin": 17, "mode": "OUT"})
```

### 3. Configuration Management

UnitMCP uses YAML for configuration management:

```yaml
# Example configuration (config.yaml)
devices:
  led1:
    type: led
    pin: 17
    active_high: true
  button1:
    type: button
    pin: 27
    pull_up: true
```

```python
# Loading configuration
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Set up devices from configuration
for name, device_config in config["devices"].items():
    device_manager.add_device(name, device_config)
```

## Using with Orchestrator

The basic examples can be easily managed and executed using the UnitMCP Orchestrator:

### Running via Orchestrator Shell

```bash
# Start the orchestrator shell
python -m unitmcp.orchestrator.main

# Run the basic example with default settings
mcp> run basic

# Run with simulation mode disabled (for physical devices)
mcp> run basic --simulation=false

# Run with custom host and port
mcp> run basic --host=192.168.1.100 --port=8080

# Run with SSL enabled
mcp> run basic --ssl=true --port=8443
```

### Remote Execution

You can run the basic example on a remote device (like a Raspberry Pi):

```bash
# Run on a remote device using SSH with password authentication
mcp> run basic --simulation=false --host=192.168.188.154 --ssh-username=pi --ssh-password=raspberry

# Run on a remote device using SSH with key-based authentication
mcp> run basic --simulation=false --host=192.168.188.154 --ssh-username=pi --ssh-key-path=~/.ssh/id_rsa
```

### Using Custom Configuration

You can use custom configuration files with the orchestrator:

```bash
# Run with a custom environment file
mcp> run basic --env-file=~/my_unitmcp_configs/env/custom.env

# Run with a custom server configuration
mcp> run basic --config=~/my_unitmcp_configs/server/server.yaml
```

### Example-Specific Parameters

The basic example supports these specific parameters when run through the orchestrator:

```bash
# Set GPIO pins to use
mcp> run basic --gpio-pins=17,18,27

# Set blink duration for LED examples
mcp> run basic --blink-duration=0.5

# Set loop count for repetitive operations
mcp> run basic --loop-count=10
```

### Running from Command Line

You can also run the basic example directly from the command line without entering the interactive shell:

```bash
# Run the basic example with default settings
python -m unitmcp.orchestrator.main --run basic

# Run with custom settings
python -m unitmcp.orchestrator.main --run basic --simulation=false --host=192.168.188.154 --ssh-username=pi --ssh-password=raspberry
```

### Troubleshooting

If you encounter issues with the basic example:

1. **Port conflict**: If the default port is already in use, specify a different port
   ```bash
   mcp> run basic --port=9515
   ```

2. **Configuration file not found**: Ensure the configuration file exists or specify a custom one
   ```bash
   mcp> run basic --config=/path/to/existing/server.yaml
   ```

3. **SSH connection issues**: Verify SSH credentials and connectivity
   ```bash
   mcp> run basic --host=192.168.188.154 --ssh-username=pi --ssh-password=raspberry --ssh-port=22 --verbose
   ```

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- For hardware examples: Compatible hardware (or use simulation mode)

For simulation mode:
```bash
SIMULATION=1 python dsl_quickstart_demo.py
```

## Next Steps

After exploring these basic examples, you can:

1. Check out the [advanced examples](../advanced/README.md) for more complex use cases
2. Explore the [platform-specific examples](../platforms/README.md) for your hardware
3. Learn about [remote control](../shell_cli/README.md) using the shell interface
4. Try the [GPIO streaming examples](../rpi_control/README.md) for real-time updates

## Additional Resources

- [UnitMCP Documentation](../../docs/README.md)
- [API Reference](../../docs/api/README.md)
- [Getting Started Guide](../../docs/getting_started.md)
