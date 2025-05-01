# unitmcp SSH Tools

This directory contains Python-based SSH tools for connecting to and managing remote devices in the unitmcp project.

## Quick Start

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install paramiko python-dotenv
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

### SSH Connector

Connect to a remote device and execute a command:

```bash
./ssh_connect.py pi@192.168.1.100 raspberry -c 'ls -la'
```
```bash
./scripts/ssh_connect_wrapper.sh pi@192.168.1.100 raspberry -c 'ls -la'
```

Or start an interactive shell:

```bash
./ssh_connect.py pi@192.168.1.100 raspberry
```

### Remote Keyboard Server Installer

Install the unitmcp Remote Keyboard Server on a Raspberry Pi:

```bash
./install_remote_keyboard_server.py --host 192.168.1.100 --password raspberry
```

## Environment Variables

You can set default connection parameters in a `.env` file:

```
SSH_USER=pi
SSH_SERVER=192.168.1.100
SSH_PASSWORD=raspberry
SSH_PORT=22
SSH_IDENTITY_FILE=~/.ssh/id_rsa
SSH_VERBOSE=false

# For Remote Keyboard Server Installer
RPI_HOST=192.168.1.100
RPI_USER=pi
RPI_PASSWORD=raspberry
INSTALL_DIR=/home/pi/unitmcp
SERVER_PORT=7890
```

## Examples

Check out the example script in the examples directory:

```bash
python ../examples/ssh_connector_example.py
```

## Documentation

For detailed documentation, see [SSH Tools Documentation](../docs/ssh_tools.md).

## Features

- URL-like connection format (`user@server`)
- Password-based authentication
- Key-based authentication
- Command execution
- Interactive shell
- Verbose logging
- Remote installation of unitmcp services

## Troubleshooting

### Connection Issues

If you're having trouble connecting to a remote device:

1. Check that the host is reachable with `ping <host>`
2. Verify that SSH is running on the remote device
3. Ensure your credentials are correct
4. Try with the `-v` flag for verbose output

### Installation Issues

If the Remote Keyboard Server installation fails:

1. Check that the Raspberry Pi has internet access
2. Ensure you have sudo privileges on the remote device
3. Check disk space with `df -h`
4. Run with `--verbose` for detailed output

## License

See the project's main LICENSE file.
