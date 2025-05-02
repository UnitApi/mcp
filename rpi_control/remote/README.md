# Remote Installation Scripts

This directory contains scripts for remote installation and management of the MCP Hardware Project on Raspberry Pi devices.

## Installation Scripts

### Standard Installation

```bash
bash install.sh
```

This script will:
1. Sync the project files to the remote Raspberry Pi
2. Install system dependencies (python3-pip, python3-dev, python3-rpi.gpio, libasound2-dev)
3. Create a Python virtual environment if it doesn't exist
4. Install Python dependencies from requirements.txt

### Raspberry Pi Installation with Dependency Fix

```bash
bash install_rpi.sh
```

This script is specifically designed to fix dependency conflicts with the `unitmcp` package on Raspberry Pi. It will:
1. Sync the project files to the remote Raspberry Pi
2. Install system dependencies (python3-pip, python3-dev, python3-rpi.gpio)
3. Create a Python virtual environment if it doesn't exist
4. Use the `install_rpi.sh` script in the parent directory to install the local unitmcp package without problematic dependencies (acme, certbot, etc.)

This approach avoids the "ResolutionImpossible" error related to the acme package that can occur on Raspberry Pi.

## Other Scripts

- `files.sh`: Sync only the remote scripts to the Raspberry Pi
- `log.sh`: View logs from the running service
- `scp.sh`: Copy all files from the rpi_control folder and its dependencies to the Raspberry Pi
  - Usage: `bash scp.sh [user@remote_host] [remote_path] [--no-replace]`
  - By default, this script will replace (overwrite) existing files on the remote machine
  - Use the `--no-replace` option to skip files that already exist on the remote machine
  - The script copies:
    1. The src directory containing the unitmcp package
    2. Essential setup files (setup.py, setup.cfg, pyproject.toml, MANIFEST.in)
    3. The entire rpi_control directory with all its files
- `start.sh`: Start the MCP Hardware Client on the Raspberry Pi
- `start_service.sh`: Start the MCP Hardware Client as a background service on the Raspberry Pi

## Configuration

All scripts use the `.env` file in the project root for configuration. Make sure to set the following variables:

- `RPI_USERNAME`: Username for SSH connection to the Raspberry Pi
- `RPI_HOST`: Hostname or IP address of the Raspberry Pi
- `REMOTE_PATH`: Path on the Raspberry Pi where the project will be installed

Example `.env` configuration:
```
RPI_USERNAME=pi
RPI_HOST=raspberrypi.local
REMOTE_PATH=/home/pi/mcp_deploy
```
