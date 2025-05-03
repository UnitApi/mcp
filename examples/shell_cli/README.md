# Shell CLI Examples

This directory contains examples of using the UnitMCP Shell CLI for remote device control.

## Overview

The Shell CLI examples demonstrate how to:
- Set up an interactive shell for hardware control
- Connect to remote devices via TCP or SSH
- Control GPIO pins and LEDs remotely
- Create custom command sequences

## Files

- `shell_cli_demo.py` - Interactive shell demo with hardware control commands
- `simple_remote_shell.py` - Lightweight shell for remote device control
- `server.py` - Example server for remote connections
- `client.py` - Example client for connecting to remote servers

## Running the Interactive Shell

```bash
# Run with examples
python shell_cli_demo.py --examples

# Run in interactive mode
python shell_cli_demo.py --interactive
```

## Remote Server and GPIO Control

You can start a remote server and then connect to it to control GPIO pins. This is particularly useful for controlling Raspberry Pi GPIO remotely.

### Starting the Server

```bash
# Start the server on the device with GPIO pins (e.g., Raspberry Pi)
python server.py --config config/server.yaml
```

### Connecting with Simple Remote Shell

```bash
# Connect via TCP
python simple_remote_shell.py --host <server_ip> --port 8000

# Connect via SSH (requires paramiko)
python simple_remote_shell.py --host <server_ip> --port 22 --ssh
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

## Simulation Mode

All examples support simulation mode for testing without hardware:

```bash
# Run in simulation mode
SIMULATION=1 python shell_cli_demo.py --interactive

# Or with the remote shell
SIMULATION=1 python simple_remote_shell.py
