# UnitMCP Orchestrator Shell Patch

This patch fixes several issues with the UnitMCP Orchestrator Shell:

1. **Connection Issues**: Fixes the async connection warning by properly handling the async client
2. **File Upload**: Adds the missing `upload` command to transfer files to a Raspberry Pi
3. **Audio Examples**: Improves support for running audio examples with demo parameters
4. **Connection Beeps**: Adds audio feedback when connecting to a Raspberry Pi

## Usage

### Running the Patched Shell

```bash
# From the project root directory
python -m unitmcp.orchestrator.shell_patch

# For minimal logging
python -m unitmcp.orchestrator.shell_patch --quiet
```

### Connecting to a Raspberry Pi

```
mcp> connect 192.168.188.154 9515
```

Upon successful connection, you'll hear a confirmation beep (if audio is available).

### Uploading Files

The patched shell adds file upload functionality:

```
# Upload a single file
mcp (192.168.188.154:9515)> upload examples/audio/tone_generator.py /home/pi/tone_generator.py

# Upload a directory and all its contents
mcp (192.168.188.154:9515)> upload examples/audio/music/ /home/pi/music/
```

### Running Audio Examples

The patched shell provides better support for running audio examples:

```
# Run a tone generator demo
mcp (192.168.188.154:9515)> run audio --demo=tone --frequency=1000 --duration=3

# Run an alarm demo
mcp (192.168.188.154:9515)> run audio --demo=alarm --volume=0.8

# Run the music player
mcp (192.168.188.154:9515)> run audio --example=music_player --config=/home/pi/music_config.yaml
```

## Fixed Issues

### 1. Connection Issues

The original shell had an issue with the async client connection:

```
/home/tom/github/UnitApi/mcp/src/unitmcp/orchestrator/orchestrator.py:396: RuntimeWarning: coroutine 'MCPHardwareClient.connect' was never awaited
  client.connect()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
```

This patch properly handles the async connection by running it in an event loop.

### 2. Missing Upload Command

The original shell didn't implement the `upload` command, resulting in:

```
mcp (192.168.188.154:9515)> upload generated_tone.wav /home/pi/music/
*** Unknown syntax: upload generated_tone.wav /home/pi/music/
```

This patch adds the `upload` command to transfer files to a Raspberry Pi.

### 3. Audio Example Parameters

The original shell didn't properly handle audio example parameters like `--demo=tone` and `--frequency=1000`. This patch improves support for these parameters.

## Dependencies

The patched shell requires:
- Python 3.6+
- paramiko (for SSH file transfers)
- colorama (for colored terminal output)

For audio feedback, the following are recommended:
- sounddevice
- numpy

## Installation

No installation is required. The patched shell is ready to use from the source directory.

## Implementation Details

The patch:
1. Creates a subclass of the original `OrchestratorShell` class
2. Overrides the `do_connect`, `do_upload`, and `do_run` methods
3. Properly handles async connections using event loops
4. Adds file upload functionality using paramiko
5. Integrates with the connection beep module for audio feedback
