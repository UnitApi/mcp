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

## Running Speaker Example with MCP Server and Client

To play an audio file (e.g. test.wav or sample_tone.wav) on the MCP hardware server using the speaker example, you can use the provided script to automatically start the server (if not already running), run the client, and stop the server when done.

### Usage

```bash
# Make sure you are in the rpi_control directory
chmod +x run_speaker_with_server.sh

# Local execution
./run_speaker_with_server.sh --host 0.0.0.0 --port 8081 --file test.wav

# Remote execution
./run_speaker_with_server.sh --remote-host raspberrypi --remote-user pi --remote-dir /home/pi/audio_server --file test.wav
```

#### Command Line Arguments
- `--host`: The host address to bind the server to (default: 0.0.0.0)
- `--port`: The port to use for the server (default: 8081)
- `--file`: The audio file to play (default: test.wav)
- `--remote-host`: Remote host to run the server on (for remote execution)
- `--remote-user`: Username for SSH connection to remote host
- `--remote-dir`: Directory on remote host to use (default: /tmp/audio_server)
- `--help`: Show help message

#### Local Mode
When no remote host is specified, the script runs in local mode:
- The server is started on the local machine
- The client connects to the local server
- Audio is played through the local machine's audio output

#### Remote Mode
When a remote host is specified, the script runs in remote mode:
- The necessary files (server script, client script, audio file) are copied to the remote host
- The server is started on the remote machine
- The client runs on the remote machine and connects to the remote server
- Audio is played through the remote machine's audio output
- All logs are retrieved from the remote machine and displayed locally

#### Notes
- If you use `--file test.wav` and the file does not exist, it will be generated automatically.
- The script checks if a server is already running at the specified host/port. If not, it starts a new server, waits for it to become ready, and then runs the client with the audio file.
- When the client finishes, the server is stopped if it was started by the script.

### Example Output
```
[LOG] Using server: 0.0.0.0:8081, client will connect to: 127.0.0.1:8081
[LOG] Starting simplified server at 0.0.0.0:8081...
[LOG] Server started with PID 371118, logs in server.log
[LOG] Waiting for server to become ready...
[LOG] Server is ready.
[LOG] Playing test.wav on server...
[LOG] Playback request sent successfully.
```

### Enhanced Logging

The script now provides comprehensive logging to help diagnose issues across both local and remote machines:

#### Log Files
- `speaker_script.log`: Main script log with timestamped entries
- `server.log`: Detailed server logs including system information and connection details
- `client.log`: Detailed client logs including playback attempts and results

#### System Information Logging
The script automatically logs detailed system information including:
- Hostname and OS details
- Available IP addresses
- Audio devices detected via `aplay -l`
- Python version
- Available disk space

#### Server Logs
Server logs include:
- Detailed startup information
- System environment details
- Connection tracking (client connects/disconnects)
- Audio playback attempts and results
- Error details with full stack traces when available

#### Client Logs
Client logs include:
- Connection attempts and results
- Command details sent to the server
- Responses received from the server
- Local playback details when applicable

This enhanced logging makes it much easier to diagnose issues, especially when running on remote Raspberry Pi devices or in distributed environments.

### Simplified Audio Server

The package includes a simplified audio server (`examples/simple_server.py`) that doesn't require complex dependencies. This server:

- Listens on the specified host/port
- Accepts JSON commands for audio playback
- Provides detailed logging
- Can be run directly or via the `run_speaker_with_server.sh` script

### Simplified Audio Client

The package also includes a simplified audio client (`examples/simple_client.py`) that:

- Connects to the server
- Sends commands to play audio files
- Can play audio locally or request remote playback
- Provides detailed error reporting

### Troubleshooting
- If the server fails to start, check the `server.log` file for error details.
- If the client fails to connect, ensure the server is running and the host/port settings are correct.
- For playback issues, check the `client.log` file for error messages.

## Hardware Control Script

The `run_hardware_with_server.sh` script provides a robust way to control hardware on a Raspberry Pi. This script can run both locally and remotely, and supports GPIO and I2C operations with enhanced reliability features.

### Key Features

- **Robust Server Management**: Automatically starts, verifies, and manages the hardware server
- **Reliable GPIO Control**: Includes retry mechanisms and comprehensive error handling
- **Detailed Logging**: Provides extensive logging for troubleshooting
- **Remote Execution**: Can run on a remote Raspberry Pi via SSH
- **Configurable**: Uses environment variables (.env file) or command-line options

### Usage

```bash
# Basic usage (uses .env file for configuration)
./run_hardware_with_server.sh

# Get hardware status
./run_hardware_with_server.sh --command status

# Control a GPIO pin
./run_hardware_with_server.sh --command gpio --pin 18 --state on

# Read from an I2C device
./run_hardware_with_server.sh --command i2c --address 0x48 --register 0x00

# Write to an I2C device
./run_hardware_with_server.sh --command i2c --address 0x48 --register 0x00 --value 0x42

# Run in local mode (even if remote settings exist in .env)
./run_hardware_with_server.sh --local

# Run on a specific remote host
./run_hardware_with_server.sh --remote-host raspberrypi --remote-user pi
```

### Command-line Options

- `--host HOST`: Host to bind the server to (default: 0.0.0.0)
- `--port PORT`: Port to use for the server (default: from .env or 8082)
- `--command COMMAND`: Hardware command to execute (default: status)
- `--pin PIN`: GPIO pin number (for gpio command)
- `--state STATE`: GPIO pin state (on/off, for gpio command)
- `--address ADDRESS`: I2C device address (for i2c command)
- `--register REGISTER`: I2C register (for i2c command)
- `--value VALUE`: I2C value to write (for i2c command)
- `--remote-host HOST`: Remote host to run the server on
- `--remote-user USER`: Username for SSH connection to remote host
- `--remote-dir DIR`: Directory on remote host to use
- `--local`: Force local mode even if remote settings exist in .env
- `--help`: Show help message

### Environment Variables

The script can be configured using a `.env` file with the following variables:

```
# Remote host configuration
RPI_HOST=192.168.1.100
RPI_USERNAME=pi
RPI_PORT=8082

# GPIO configuration
GPIO_PIN=17

# I2C configuration
I2C_ADDRESS=0x48
I2C_REGISTER=0x00
I2C_VALUE=0x42
```

### Special GPIO Status Command

When running the status command with a PIN specified, the script will:
1. Execute the status command to get hardware information
2. Toggle the specified GPIO pin (HIGH then LOW)
3. Provide detailed logs of the GPIO state changes

Example:
```bash
./run_hardware_with_server.sh --command status --pin 18
```

### Reliability Features

The script includes several reliability enhancements:

1. **Server Startup Verification**:
   - Uses `nohup` to ensure the server keeps running after SSH disconnects
   - Verifies the server is listening on the specified port
   - Implements timeout mechanisms to prevent hanging

2. **GPIO Command Retry Mechanism**:
   - Automatically retries failed GPIO commands
   - Verifies server status before each GPIO operation
   - Restarts the server if it's not running

3. **Comprehensive Error Handling**:
   - Detailed error messages for all operations
   - Server log retrieval for troubleshooting
   - Exit codes that reflect the success or failure of operations

4. **Detailed Logging**:
   - Timestamped logs for all operations
   - System information logging
   - Command execution and response logging

### Troubleshooting

If you encounter issues with the hardware control script:

1. **Check the Logs**:
   - The script creates a `hardware_script.log` file with detailed information
   - Server logs are available in `hardware_server.log`
   - Client logs are available in `hardware_client.log`

2. **Verify Connectivity**:
   - Ensure you can SSH to the remote host without password (using SSH keys)
   - Check that the specified port is not blocked by a firewall

3. **Check GPIO Access**:
   - Ensure the user has permission to access GPIO pins (usually requires being in the 'gpio' group)
   - Verify that the GPIO library is installed correctly

4. **Server Issues**:
   - If the server fails to start, check for port conflicts
   - Ensure Python and required libraries are installed on the remote host

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
  # Edit .env to set REMOTE, REMOTE_PATH, RPI_USERNAME, etc.
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
  This will install all required system and Python dependencies in a Python virtual environment (`venv`).
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


# Raspberry Pi Simulation Docker Environment

This directory contains a Docker Compose setup for simulating a Raspberry Pi environment for testing. The setup includes three containers:

1. **rpi-simulator**: A container that simulates a Raspberry Pi with GPIO, camera, audio, and other hardware capabilities
2. **llm-model**: A container running a small LLM model (Ollama) that could run on a Raspberry Pi
3. **test-client**: A client container that connects to both the Raspberry Pi simulator and the LLM model to enable testing

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic knowledge of Docker and containerization
- Understanding of the UnitMCP hardware control system

## Directory Structure

```
docker/
├── client/                 # Test client container files
│   ├── Dockerfile          # Client container definition
│   └── llm_client.py       # LLM client implementation for testing
├── llm/                    # LLM model container files
│   └── Dockerfile          # LLM container definition
├── rpi/                    # Raspberry Pi simulator container files
│   ├── Dockerfile          # Raspberry Pi simulator container definition
│   └── hardware_server.py  # Raspberry Pi hardware server implementation
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```



## Getting Started

### 1. Build and Start the Containers

From the `rpi_control/docker` directory, run:

```bash
docker-compose up --build
```

This will build and start all three containers:
- `rpi-simulator`: The Raspberry Pi simulator
- `llm-model`: The Ollama LLM server
- `test-client`: The client that connects to both servers for testing

### 2. Interact with the System

Once the containers are running, you can interact with the system through the `test-client` container. The client provides a command-line interface where you can type natural language commands to control the simulated Raspberry Pi.

Example commands:
- "Turn on the LED on pin 17"
- "Blink the LED on pin 18"
- "Take a picture with the camera"
- "Record audio for 5 seconds"
- "Read the temperature"
- "Convert 'Hello, world!' to speech"

### 3. Stop the Containers

To stop the containers, press `Ctrl+C` in the terminal where you started Docker Compose, or run:

```bash
docker-compose down
```

## Configuration

### Environment Variables

You can configure the system using environment variables in the `docker-compose.yml` file:

#### Raspberry Pi Simulator
- `HOST`: The hostname to bind the server to (default: `0.0.0.0`)
- `PORT`: The port to listen on (default: `8080`)
- `SERVER_NAME`: The name of the MCP server (default: `Raspberry Pi Simulator`)

#### Test Client
- `RPI_HOST`: The hostname of the Raspberry Pi simulator (default: `rpi-simulator`)
- `RPI_PORT`: The port of the Raspberry Pi simulator (default: `8080`)
- `OLLAMA_HOST`: The hostname of the Ollama server (default: `llm-model`)
- `OLLAMA_PORT`: The port of the Ollama server (default: `11434`)
- `OLLAMA_MODEL`: The LLM model to use (default: `llama2`)

## Simulated Hardware

The Raspberry Pi simulator provides the following simulated hardware devices:

### GPIO
- Virtual LEDs that can be turned on, off, or blinked
- Virtual buttons that can be pressed and released
- General GPIO pins that can be set up as input or output

### Camera
- Virtual camera that simulates image capture

### Audio
- Virtual microphone for audio recording
- Text-to-speech simulation

### Sensors
- Virtual temperature sensor

## Extending the System

### Adding New Simulated Hardware

To add new simulated hardware devices, modify the `hardware_server.py` file in the `rpi` directory. You can add new tools to the LLM server by implementing them in the `_register_custom_tools` method of the `RaspberryPiSimulator` class.

### Using Different LLM Models

The system uses Ollama as the LLM provider, which supports various models. You can change the model by setting the `OLLAMA_MODEL` environment variable in the `docker-compose.yml` file. The default model is `llama2`.

For Raspberry Pi compatibility, consider using smaller models like:
- `llama2`
- `orca-mini`
- `phi`
- `gemma:2b`
- `tinyllama`

## Troubleshooting

### Connection Issues

If the client cannot connect to the Raspberry Pi simulator or the Ollama server, check the following:
- Ensure all containers are running (`docker-compose ps`)
- Check the logs for error messages (`docker-compose logs`)
- Verify the network configuration in `docker-compose.yml`

### LLM Issues

If the LLM is not responding correctly:
- Check if the model is available (`docker exec -it llm-model ollama list`)
- Try using a different model by setting the `OLLAMA_MODEL` environment variable
- Increase the timeout values in the client code if needed

## License

This project is licensed under the Apache2 License. See the [LICENSE](LICENSE) file for details.