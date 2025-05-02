# Raspberry Pi Control (rpi_control)

This directory contains examples and scripts for controlling Raspberry Pi GPIO and hardware using the MCP Hardware Project.

## Installation

### Standard Installation

To install all dependencies on your Raspberry Pi (or remote machine), run:

```bash
bash install.sh
```

This will install Python dependencies and system packages required for GPIO and MCP hardware access.

### Raspberry Pi Installation (Dependency Fix)

If you encounter dependency conflicts with the `unitmcp` package on Raspberry Pi, use the special installation script:

```bash
bash install_rpi.sh
```

This script will:
1. Install the required system dependencies (including ffmpeg for audio processing)
2. Install Python dependencies from requirements.txt
3. Install the local unitmcp package without problematic dependencies (acme, certbot, etc.)

This approach avoids the "ResolutionImpossible" error related to the acme package that can occur on Raspberry Pi.

#### System Dependencies

The installation script will install these system dependencies:
- libasound2-dev (required for simpleaudio)
- ffmpeg (required for audio processing with pydub)

If you're installing manually, make sure to install these dependencies:
```bash
sudo apt-get update
sudo apt-get install -y libasound2-dev ffmpeg
```

## Usage

To install and start a demo client in one step:

```bash
bash start.sh
```

To run a specific example client:

```bash
bash client.sh
```
Edit `client.sh` to select which example to run (default: full_demo.py).

## .env Configuration

All Python and shell scripts in this project use a `.env` file for configuration.

- Copy `env.sample` to `.env` and edit as needed:
  ```bash
  cp env.sample .env
  ```
- Set variables such as:
  - `RPI_HOST`, `RPI_USERNAME`, `RPI_PORT`: Raspberry Pi connection info for Python examples
  - `REMOTE`, `REMOTE_PATH`: Used by `install_remote.sh` for remote installation
  - `SCRIPT_DIR`: Used by `start.sh` and `client.sh` to set the working directory

**Example .env:**
```ini
RPI_HOST=raspberrypi
RPI_USERNAME=pi
RPI_PORT=8080
REMOTE=pi@raspberrypi
REMOTE_PATH=~/pi
SCRIPT_DIR=./rpi_control
```

All examples and shell scripts will automatically use these variables.

## Remote Installation

To install `rpi_control` on a remote Raspberry Pi (or any remote Linux machine) via SSH:

```bash
bash install_remote.sh user@remote_host [remote_path]
```
- `user@remote_host`: SSH target (e.g., pi@192.168.1.42)
- `[remote_path]`: (Optional) Path on remote (default: `~/rpi_control`)

This will:
1. Copy all files to the remote directory
2. Run `install.sh` on the remote

## Folder Structure

- `remote/`: Scripts and files to be deployed and run on the Raspberry Pi
    - `install.sh`: Installs system and Python dependencies in a venv
    - `requirements.txt`: Python dependencies for the Pi
    - `files.sh`, `scp.sh`, `start.sh`: Utility scripts for remote management
- `examples/`: Python example scripts for MCP hardware control
- `.env`: Project-wide configuration (keep this in the project root)

## Quick Start

### 1. Sync Project to Raspberry Pi

- Make sure your project directory contains `.env`, `remote/`, `examples/`, etc.
- From your local machine, sync the entire project to your Pi (replace `pi@192.168.188.154` with your Pi's address):

  ```bash
  rsync -avz --exclude 'venv' --exclude '.git' --exclude '__pycache__' . pi@192.168.188.154:/home/pi/
  ```

### 2. Install Dependencies on the Pi

- SSH into your Pi:
  ```bash
  ssh pi@192.168.188.154
  cd remote
  bash install.sh
  ```
- This will set up a Python virtual environment and install all dependencies.

### 3. Run All Examples on the Pi

- Still in the `remote` directory, start all examples (or those listed in `$EXAMPLES` in `.env`):
  ```bash
  bash start.sh
  ```

### 4. Sync Only Remote Scripts (optional)

- To sync just the `remote/` folder:
  ```bash
  bash remote/files.sh
  ```

---

**Project structure on the Pi should look like:**
```
/home/pi/
  .env
  remote/
  examples/
  ...
```

- `.env` must be in `/home/pi/` (the project root).
- All scripts expect this structure for correct operation.

---

For troubleshooting, see script output and comments in each script.

## Usage

### 1. Configure Environment

- Copy `env.sample` to `.env` in the project root and edit as needed:
  ```bash
  cp env.sample .env
  # Edit .env to set REMOTE, REMOTE_PATH, RPI_USERNAME, etc.
  ```

### 2. Sync Files to Remote (Manual)

- You can use `scp` or `rsync` to copy files from your local machine to the Pi, or use the provided scripts in `remote/` (e.g., `scp.sh`, `files.sh`).

### 3. Install on the Raspberry Pi

- SSH into your Raspberry Pi:
  ```bash
  ssh pi@<your_rpi_ip>
  ```
- Go to the `remote` directory and run:
  ```bash
  cd remote
  bash install.sh
  ```
  This will install all required system and Python dependencies in a virtual environment (`venv`).
- To use the environment later, activate it with:
  ```bash
  source venv/bin/activate
  ```

---

**Note:**
- Keep `.env` in the project root (not in `remote/`).
- The `local/` folder is not present by default; you may create it for your own sync scripts if desired.

## Examples

- `examples/full_demo.py`: Complete workflow demo (LED control + audio recording)
- `examples/audio_record.py`: Record audio using MCP Hardware Client
- `examples/led_control.py`: Control an LED using MCP Hardware Client
- `examples/mqtt_example.py`: Use MQTT bridge for MCP hardware access
- `examples/rpi_control.py`: Advanced GPIO and hardware control (multiple demos)
- `examples/hello_world.py`: Minimal test example
- `examples/play_audio_unitmcp.py`: Play a .wav or .mp3 file on the remote device using MCP Hardware Client
- `examples/play_sample_audio.sh`: Shell script to generate and play a sample audio tone (useful for testing audio setup)

---

For more details, see comments in each script and the `.env` file.

## Audio Playback on Remote Device

You can play audio files on the remote Raspberry Pi using the MCP Hardware Client:

```bash
python3 examples/play_audio_unitmcp.py --file examples/test.wav
```

If you do not specify `--file`, the script will use the defaults set in your `.env` file (`DEFAULT_WAV` or `DEFAULT_MP3`).

Example `.env` entries:
```
DEFAULT_MP3=test.mp3
DEFAULT_WAV=test.wav
```

To play audio locally (on the device running the script) instead, use:

```bash
python3 examples/speaker_control.py --file examples/test.wav
```

### Sample Audio Script

For a quick test of audio playback, use the provided sample script:

```bash
cd examples
bash play_sample_audio.sh
```

This script will:
1. Check if ffmpeg is installed and install it if needed
2. Create a sample audio file (3-second 440Hz tone)
3. Play the sample audio using speaker_control.py

## Remote Deployment and Service Management

This project supports fully automated remote deployment and example service management via SSH.

### 1. Configure `.env`
Copy `env.sample` to `.env` and edit as needed. Important variables:
- `RPI_USERNAME` and `RPI_HOST`: Remote SSH credentials
- `EXAMPLE`: Example script to run as a service (e.g. `full_demo.py`)
- `EXAMPLES_DIR`: Directory on the remote where examples are stored
- `PORT`: Port used by the example (for freeing up with `fuser`)
- `LOGFILE`: Log file name for the service output

### 2. Install/Update Code and Dependencies Remotely
From your project root, run:

For standard installation:
```bash
bash rpi_control/remote/install.sh
```

For Raspberry Pi installation with dependency fix:
```bash
bash rpi_control/remote/install_rpi.sh
```

Both scripts will sync your project to the remote host and install all dependencies in a Python virtual environment. The `install_rpi.sh` script specifically avoids dependency conflicts with the `unitmcp` package on Raspberry Pi.

### 3. Start Example Service Remotely
```bash
bash rpi_control/remote/start_service.sh
```
This will SSH to the remote, free the specified port, and start the selected example as a background service. Output is logged to `$LOGFILE` in `$EXAMPLES_DIR`.

### 4. Show Service Logs
```bash
bash rpi_control/remote/show_log.sh
```
This will SSH to the remote and show the last 50 lines of the log file for your running service.

---

**Tip:** All scripts use `.env` for configuration, so you can easily switch examples, ports, and log files by editing `.env`.

For advanced automation or troubleshooting, see the comments in each script.

## File Overview

- `install.sh`: Install all dependencies (Python/system)
- `start.sh`: Install then run a demo client
- `client.sh`: Run a client example (edit to select)
- `install_remote.sh`: Copy and install rpi_control on a remote machine via SSH

## Requirements

- Raspberry Pi hardware
- MCP hardware package (see https://github.com/UnitApi/mcp-hardware)
- Python 3.7+

---

For more info, see the MCP Hardware Project: https://github.com/UnitApi/mcp-hardware
