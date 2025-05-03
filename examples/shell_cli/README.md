# Shell CLI Examples

This directory contains examples of using the UnitMCP Shell CLI for remote device control.

## Overview

The Shell CLI examples demonstrate how to:
- Set up an interactive shell for hardware control
- Connect to remote devices via TCP or SSH
- Control GPIO pins and LEDs remotely
- Create custom command sequences
- Monitor and manage remote processes

## Files in this Directory

- `simple_remote_shell.py` - A lightweight shell for connecting to and controlling remote devices
- `refactored_remote_shell.py` - An improved version with better error handling and resource management
- `process_manager.py` - Utility for monitoring and managing remote processes
- `runner.py` - Script for running the shell in non-interactive mode

## Using Simple Remote Shell

The `simple_remote_shell.py` script provides a lightweight shell for connecting to and controlling remote devices, particularly Raspberry Pi.

### Starting the Shell

```bash
# Basic usage
python simple_remote_shell.py

# Connect via TCP
python simple_remote_shell.py --host 192.168.1.100 --port 8888

# Connect via SSH
python simple_remote_shell.py --host 192.168.1.100 --port 22 --ssh --username pi

# Run in simulation mode
python simple_remote_shell.py --simulation
```

### Command Line Arguments

- `--host` - Hostname or IP address (default: localhost)
- `--port` - Port number (default: 22 for SSH, 8888 for TCP)
- `--ssh` - Use SSH for connection (default: False)
- `--username` - SSH username (default: pi)
- `--key-path` - Path to SSH key file (default: ~/.ssh/id_rsa)
- `--simulation` - Run in simulation mode (default: False)
- `--log-file` - Path to log file (default: None)
- `--log-level` - Logging level (default: INFO)

### Available Commands

Once you see the `(remote)` prompt, you have successfully connected to your remote device. Here are the commands you can use:

#### Connection Management

```
# Connect to a remote device
(remote) connect 192.168.1.100 8888
(remote) connect 192.168.1.100 22 --ssh --username pi --key-path ~/.ssh/id_rsa

# Disconnect from the current device
(remote) disconnect
```

#### Basic Shell Commands

```
# Get help
(remote) help

# Get help for a specific command
(remote) help gpio

# Exit the shell
(remote) exit
(remote) quit

# Clear the screen
(remote) clear
```

#### GPIO Control

```
# List all available GPIO pins
(remote) gpio list

# Set GPIO pin mode and state
(remote) gpio 18 out 1    # Set GPIO 17 as output with value HIGH
(remote) gpio 18 in       # Set GPIO 18 as input
(remote) gpio 17 read     # Read the current value of GPIO 17
(remote) gpio 18 toggle   # Toggle the state of GPIO 17
```

#### LED Control

```
# Set up an LED on a GPIO pin
(remote) led led1 setup 17

# Turn LED on/off
(remote) led led1 on
(remote) led led1 off

# Make LED blink
(remote) led led1 blink 0.5 0.5  # Blink with 0.5s on, 0.5s off

# Stop LED blinking
(remote) led led1 stop

# List all configured LEDs
(remote) led list
```

#### Button Control

```
# Set up a button on a GPIO pin
(remote) button btn1 setup 18

# Read button state
(remote) button btn1 read

# Monitor button presses
(remote) button btn1 monitor

# Stop monitoring
(remote) button btn1 stop

# List all configured buttons
(remote) button list
```

#### Hardware Control

```
# List all available hardware components
(remote) hardware list

# Get hardware information
(remote) hardware info <component>

# Control hardware component
(remote) hardware <component> <action> [parameters]
```

#### Remote Command Execution

```
# Execute a command on the remote device
(remote) exec ls -la
(remote) exec python /path/to/script.py

# Run a command in the background
(remote) exec-bg python long_running_script.py
```

#### Variable Management

```
# Set a variable
(remote) set pin_number 17

# Get a variable value
(remote) get pin_number

# List all variables
(remote) list
```

## Using Refactored Remote Shell

The `refactored_remote_shell.py` script is an improved version of the simple remote shell with better error handling, resource management, and logging.

### Starting the Shell

```bash
# Basic usage
python refactored_remote_shell.py

# Connect via TCP
python refactored_remote_shell.py --host 192.168.1.100 --port 8888

# Connect via SSH
python refactored_remote_shell.py --host 192.168.1.100 --port 22 --ssh --username pi

# Run in simulation mode
python refactored_remote_shell.py --simulation

# Specify log file and level
python refactored_remote_shell.py --log-file shell.log --log-level DEBUG
```

### Key Improvements

- **Standardized Error Handling**: Uses the UnitMCP exception hierarchy
- **Resource Management**: Properly manages and cleans up resources
- **Improved Logging**: Configurable logging with different levels
- **Process Monitoring**: Monitors and manages remote processes
- **Graceful Degradation**: Works even when UnitMCP utilities are not available

### Additional Commands

The refactored shell includes all commands from the simple shell, plus:

```
# Connect with more options
(remote) connect 192.168.1.100 8888 --ssh --username admin --key-path ~/.ssh/custom_key --password mypassword

# Execute a command with timeout
(remote) exec-timeout 10 long_running_command

# Monitor system resources
(remote) monitor cpu
(remote) monitor memory
(remote) monitor temp
```

## Using the Process Manager

The `process_manager.py` script provides utilities for monitoring and managing processes on the remote device.

### Features

- **Process Monitoring**: Tracks running processes
- **Anomaly Detection**: Identifies hung or resource-intensive processes
- **Automatic Recovery**: Can terminate problematic processes
- **Resource Contention**: Detects and resolves resource conflicts

### Usage in Shell Scripts

```python
from process_manager import get_instance

# Get the process manager instance
process_manager = get_instance()

# Register a process
process_id = process_manager.register_process("my_process", pid=12345)

# Check for anomalies
fixed, remaining = process_manager.handle_anomalies(auto_fix=True)

# Clean up a process
process_manager.cleanup_process(process_id)
```

## Environment Variables

The shell scripts support the following environment variables:

```
# Host and port for connection
SERVER_HOST=192.168.1.100
SERVER_PORT=8888

# SSH settings
SSH_USERNAME=pi
SSH_KEY_PATH=~/.ssh/id_rsa

# Simulation mode
SIMULATION=1

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=shell.log
```

## Examples

### Basic Connection and GPIO Control

```bash
# Start the shell
python simple_remote_shell.py

# In the shell
(remote) connect 192.168.1.100 8888
(remote) gpio 17 out 1
(remote) gpio 18 in
(remote) gpio 18 read
```

### LED Blinking Example

```bash
# Start the shell
python simple_remote_shell.py --host 192.168.1.100 --port 8888

# In the shell
(remote) led led1 setup 17
(remote) led led1 blink 0.5 0.5
# Wait a few seconds to see the LED blinking
(remote) led led1 stop
```

### Button Monitoring Example

```bash
# Start the shell
python simple_remote_shell.py --host 192.168.1.100 --port 8888

# In the shell
(remote) button btn1 setup 18
(remote) button btn1 monitor
# Press the button to see events
# Press Ctrl+C to stop monitoring
```

### Running in Non-Interactive Mode

```bash
# Create a script file
echo "connect 192.168.1.100 8888
gpio 17 out 1
sleep 1
gpio 17 out 0
exit" > commands.txt

# Run the shell with the script
cat commands.txt | python simple_remote_shell.py
```

### Using Environment Variables

```bash
# Set environment variables
export SERVER_HOST=192.168.1.100
export SERVER_PORT=8888
export SIMULATION=1

# Run the shell
python simple_remote_shell.py
```

## Integration with UnitMCP

The shell CLI examples can be integrated with the UnitMCP framework for more advanced functionality:

```python
from unitmcp.utils import ResourceManager, configure_logging
from unitmcp.hardware import DeviceManager

# Configure logging
configure_logging(level="INFO", log_file="shell.log")

# Create a resource manager
with ResourceManager() as rm:
    # Create a device manager
    device_manager = DeviceManager()
    
    # Register the device manager with the resource manager
    rm.register(device_manager, cleanup_func=device_manager.cleanup)
    
    # Use the device manager
    device_manager.setup_device("led1", "LED", pin=17)
    device_manager.control_device("led1", "on")
```

## Using the Orchestrator

For more advanced management of examples and servers, see the [Orchestrator README](../orchestrator/README.md).
