# UnitMCP Enhanced Orchestrator Shell

This extension adds advanced features to the UnitMCP Orchestrator Shell, including:

1. **Connection Beeps** - Audio feedback when connecting to a Raspberry Pi
2. **File Upload** - Upload files and directories to a remote Raspberry Pi
3. **Enhanced Run Commands** - Better support for audio examples and demos

## Installation

No installation is required. The enhanced shell is ready to use from the examples directory.

## Usage

### Starting the Enhanced Shell

```bash
# From the project root directory
python -m examples.audio.enhanced_shell

# To disable connection beeps
python -m examples.audio.enhanced_shell --no-beeps

# For minimal logging
python -m examples.audio.enhanced_shell --quiet
```

### Connecting to a Raspberry Pi

```
mcp> connect 192.168.188.154 9515
```

Upon successful connection, you'll hear a confirmation beep.

### Uploading Files

The enhanced shell adds file upload functionality:

```
# Upload a single file
mcp (192.168.188.154:9515)> upload examples/audio/tone_generator.py /home/pi/tone_generator.py

# Upload a directory and all its contents
mcp (192.168.188.154:9515)> upload examples/audio/music/ /home/pi/music/
```

### Running Audio Examples

The enhanced shell provides better support for running audio examples:

```
# Run a tone generator demo
mcp (192.168.188.154:9515)> run audio --demo=tone --frequency=1000 --duration=3

# Run an alarm demo
mcp (192.168.188.154:9515)> run audio --demo=alarm --volume=0.8

# Run the music player
mcp (192.168.188.154:9515)> run audio --example=music_player --config=/home/pi/music_config.yaml
```

### Available Commands

Type `help` to see all available commands:

```
mcp> help
```

For detailed help on a specific command:

```
mcp> help upload
```

## Features

### Connection Beeps

The enhanced shell plays audio feedback when:
- Successfully connecting to a Raspberry Pi (high-pitched beep)
- Failed connection attempts (two low-pitched beeps)

### File Upload

The `upload` command supports:
- Single file uploads
- Directory uploads (recursively)
- Automatic creation of target directories

### Enhanced Run Command

The enhanced run command provides:
- Better support for audio examples
- Clearer output and status information
- Support for all audio demo parameters

## Troubleshooting

### No Sound on Connection

If you don't hear beeps when connecting:
1. Make sure your audio device is properly configured
2. Check if the `sounddevice` Python package is installed
3. Try running with `--no-beeps` to disable audio feedback

### Upload Failures

If file uploads fail:
1. Verify that the Raspberry Pi is accessible
2. Check SSH credentials and permissions
3. Ensure target directories are writable

## Dependencies

The enhanced shell requires:
- Python 3.6+
- sounddevice (for audio feedback)
- paramiko (for SSH file transfers)
- colorama (for colored terminal output)

## Examples

### Complete Workflow Example

```
# Start the enhanced shell
python -m examples.audio.enhanced_shell

# Connect to Raspberry Pi
mcp> connect 192.168.188.154 9515

# Upload music configuration
mcp (192.168.188.154:9515)> upload examples/audio/config/music_config.yaml /home/pi/music_config.yaml

# Upload music files
mcp (192.168.188.154:9515)> upload examples/audio/music/ /home/pi/music/

# Run the music player
mcp (192.168.188.154:9515)> run audio --example=music_player --config=/home/pi/music_config.yaml --output=headphones

# Check status
mcp (192.168.188.154:9515)> status

# Disconnect when done
mcp (192.168.188.154:9515)> disconnect
```
