# Shell CLI Examples

This directory contains examples of using the UnitMCP Shell CLI for remote device control.

## Overview

The Shell CLI examples demonstrate how to:
- Set up an interactive shell for hardware control
- Connect to remote devices via TCP or SSH
- Control GPIO pins and LEDs remotely
- Create custom command sequences

## Using the Orchestrator (New Feature)

The UnitMCP Orchestrator is a new module that provides an interactive shell for managing examples and servers. It allows you to easily run examples, connect to remote servers, and monitor their status.

### Starting the Orchestrator

```bash
# Start the Orchestrator shell
python -m unitmcp.orchestrator.main
```

### Connecting to a Raspberry Pi Server

```bash
# In the Orchestrator shell
orchestrator> connect 192.168.1.100 8080
```

If you need SSL:

```bash
orchestrator> connect 192.168.1.100 8080 --ssl
```

### What to Do After Connecting to a Raspberry Pi Server

Once connected to a Raspberry Pi server, you can:

1. **Control GPIO Pins**:
   ```
   # Set GPIO pin mode and state
   orchestrator> gpio 17 out 1
   orchestrator> gpio 18 in
   orchestrator> gpio 17 read
   ```

2. **Control LEDs**:
   ```
   # Set up an LED on a GPIO pin
   orchestrator> led led1 setup 17
   
   # Turn LED on/off
   orchestrator> led led1 on
   orchestrator> led led1 off
   
   # Make LED blink
   orchestrator> led led1 blink 0.5 0.5
   ```

3. **Run Hardware Commands**:
   ```
   # List available hardware
   orchestrator> hardware list
   
   # Get hardware status
   orchestrator> hardware status
   
   # Control specific hardware components
   orchestrator> hardware <component_name> <action> [parameters]
   ```

4. **Execute Remote Commands**:
   ```
   # Execute a shell command on the remote device
   orchestrator> exec ls -la
   
   # Run a Python script on the remote device
   orchestrator> exec python /path/to/script.py
   ```

5. **Transfer Files**:
   ```
   # Upload a file to the remote device
   orchestrator> upload local_file.txt /remote/path/
   
   # Download a file from the remote device
   orchestrator> download /remote/file.txt local_path/
   ```

6. **Monitor System**:
   ```
   # Get system information
   orchestrator> system info
   
   # Monitor CPU and memory usage
   orchestrator> system monitor
   
   # Check temperature
   orchestrator> system temp
   ```

### Running Examples on Raspberry Pi

You can also run examples directly on the Raspberry Pi:

```bash
# Run an example on the connected Raspberry Pi
orchestrator> run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
```

This will:
1. Connect to the Raspberry Pi via SSH
2. Set up the necessary environment
3. Start the server
4. Monitor the progress

### Managing Multiple Servers

The Orchestrator allows you to manage multiple servers:

```bash
# List all active servers
orchestrator> servers

# Check status of running examples
orchestrator> runners

# Stop a running example
orchestrator> stop <runner_id>
```

## Using Simple Remote Shell

The `simple_remote_shell.py` script provides a lightweight shell for connecting to and controlling remote devices, particularly Raspberry Pi.

### Connecting to a Raspberry Pi

```bash
# Connect via SSH
python simple_remote_shell.py --host 192.168.188.154 --port 22 --ssh --username pi

# You should see this prompt after successful connection:
Remote Device Control Shell. Type help or ? to list commands.
(remote) 
```

### Available Commands After Connection

Once you see the `(remote)` prompt, you have successfully connected to your Raspberry Pi. Here are the commands you can use:

#### 1. Basic Shell Commands

```
(remote) help
```
Displays all available commands.

```
(remote) exit
```
Disconnects from the remote device and exits the shell.

#### 2. GPIO Control

```
(remote) gpio list
```
Lists all available GPIO pins on the Raspberry Pi.

```
(remote) gpio <pin_number> <mode> [value]
```
Controls a GPIO pin. Mode can be 'in' or 'out'. Value (for 'out' mode) can be 0 or 1.

Examples:
```
(remote) gpio 17 out 1    # Set GPIO 17 as output with value HIGH
(remote) gpio 18 in       # Set GPIO 18 as input
(remote) gpio 17 read     # Read the current value of GPIO 17
```

#### 3. LED Control

```
(remote) led <name> setup <pin_number>
```
Sets up an LED with a name on a specific GPIO pin.

```
(remote) led <name> on
```
Turns on the LED.

```
(remote) led <name> off
```
Turns off the LED.

```
(remote) led <name> blink <on_time> <off_time> [count]
```
Makes the LED blink with specified on and off times (in seconds). Optional count parameter limits the number of blinks.

Examples:
```
(remote) led status setup 17        # Set up an LED named 'status' on GPIO 17
(remote) led status on              # Turn on the status LED
(remote) led status blink 0.5 0.5   # Make the status LED blink (0.5s on, 0.5s off)
```

#### 4. Hardware Commands

```
(remote) hardware list
```
Lists all available hardware components.

```
(remote) hardware info <component>
```
Shows information about a specific hardware component.

```
(remote) hardware <component> <action> [parameters]
```
Controls a hardware component with a specific action and optional parameters.

Examples:
```
(remote) hardware camera capture image.jpg    # Capture an image with the camera
(remote) hardware sensor read temperature     # Read temperature from a sensor
```

#### 5. System Commands

```
(remote) system info
```
Shows system information (CPU, memory, disk, etc.).

```
(remote) system temp
```
Shows the CPU temperature.

```
(remote) system reboot
```
Reboots the Raspberry Pi.

```
(remote) system shutdown
```
Shuts down the Raspberry Pi.

#### 6. File Operations

```
(remote) file list <path>
```
Lists files in the specified directory.

```
(remote) file read <path>
```
Reads and displays the content of a file.

```
(remote) file write <path> <content>
```
Writes content to a file.

```
(remote) file delete <path>
```
Deletes a file.

Examples:
```
(remote) file list /home/pi            # List files in /home/pi
(remote) file read /home/pi/test.txt   # Read the content of test.txt
```

#### 7. Execute Shell Commands

```
(remote) exec <command>
```
Executes a shell command on the remote device.

Examples:
```
(remote) exec ls -la                   # List files with details
(remote) exec python3 /home/pi/test.py # Run a Python script
```

#### 8. Script Execution

```
(remote) script run <path>
```
Runs a script file containing a sequence of shell commands.

```
(remote) script record <path>
```
Starts recording commands to a script file.

```
(remote) script stop
```
Stops recording commands.

Example:
```
(remote) script record /home/pi/led_sequence.txt
(remote) led status setup 17
(remote) led status blink 0.2 0.2 10
(remote) script stop
(remote) script run /home/pi/led_sequence.txt
```

### Example Workflow

Here's a complete example workflow for controlling LEDs on your Raspberry Pi:

```
# Connect to the Raspberry Pi
python simple_remote_shell.py --host 192.168.1.2 --port 22 --ssh --username pi

# In the remote shell:
(remote) gpio list                  # See available GPIO pins
(remote) led red setup 17           # Set up a red LED on GPIO 17
(remote) led green setup 18         # Set up a green LED on GPIO 18
(remote) led red on                 # Turn on the red LED
(remote) sleep 2                    # Wait for 2 seconds
(remote) led red off                # Turn off the red LED
(remote) led green on               # Turn on the green LED
(remote) led green blink 0.3 0.3 5  # Make the green LED blink 5 times
(remote) exit                       # Exit the shell
```

### Troubleshooting

If you encounter issues with the connection:

1. **Connection Refused**: Ensure the SSH service is running on your Raspberry Pi and the IP address is correct.
   ```
   (remote) exec sudo service ssh status
   ```

2. **Permission Denied**: Ensure you're using the correct username and password.

3. **GPIO Permission Issues**: You might need to run the shell with sudo or add your user to the gpio group.
   ```
   (remote) exec sudo usermod -a -G gpio pi
   ```

4. **Command Not Found**: Some commands might require additional software. Install them with:
   ```
   (remote) exec sudo apt-get update && sudo apt-get install -y python3-rpi.gpio
   ```

## Files

- `shell_cli_demo.py` - Interactive shell demo with hardware control commands
- `simple_remote_shell.py` - Lightweight shell for remote device control
- `server.py` - Example server for remote connections
- `client.py` - Example client for connecting to remote servers
- `runner.py` - Unified runner script to manage both client and server components

## Running the Interactive Shell

```bash
# Run with examples
python shell_cli_demo.py --examples

# Run in interactive mode
python shell_cli_demo.py --interactive
```

## Using the Runner

The `runner.py` script provides a standardized way to start and manage both client and server components of the example:

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
SERVER_PORT=8000
LOG_LEVEL=INFO

# Hardware configuration
SIMULATION=1
GPIO_PINS=17,18,27
LED_PINS=17,22
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

## Remote Server and GPIO Control

You can start a remote server and then connect to it to control GPIO pins. This is particularly useful for controlling Raspberry Pi GPIO remotely.

### Starting the Server

```bash
# Start the server on the device with GPIO pins (e.g., Raspberry Pi)
python server.py --config config/server.yaml

# Start the server with custom host and port
python server.py --host 192.168.1.100 --port 8888

# Or use the runner
python runner.py --server-only
```

### Connecting with Simple Remote Shell

```bash
# Connect via TCP
python simple_remote_shell.py --host <server_ip> --port 8000

# Connect via SSH (requires paramiko)
python simple_remote_shell.py --host <server_ip> --port 22 --ssh --username pi

# Or use the runner
python runner.py --client-only
```

### Controlling GPIO Pins Remotely

Once connected, you can control GPIO pins with these commands:

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

## Configuration Files

The example uses YAML configuration files located in the `config/` directory:

- `server.yaml`: Server configuration including host, port, and available commands
- `client.yaml`: Client configuration including connection settings and command aliases

Example server configuration:
```yaml
server:
  host: 0.0.0.0
  port: 8000
  max_connections: 5
  
gpio:
  available_pins: [17, 18, 22, 27]
  default_mode: out
```

Example client configuration:
```yaml
client:
  host: localhost
  port: 8000
  timeout: 5
  
commands:
  aliases:
    led_on: "gpio 17 out 1"
    led_off: "gpio 17 out 0"
```

## Simulation Mode

All examples support simulation mode for testing without hardware:

```bash
# Run in simulation mode
SIMULATION=1 python shell_cli_demo.py --interactive

# Or with the remote shell
SIMULATION=1 python simple_remote_shell.py

# Or with the runner
SIMULATION=1 python runner.py
