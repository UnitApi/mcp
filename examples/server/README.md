# Server Examples

This directory contains examples for starting and configuring the MCP Hardware server.

## Files
- `start_server.py` — Start the MCP Hardware server with all components (GPIO, Input, Audio, Camera).

## Usage
```bash
python start_server.py
```

### Command Line Options
```bash
python start_server.py --host 127.0.0.1 --port 8888 --components gpio input audio camera
```

- `--host`: Server host address (default: 127.0.0.1)
- `--port`: Server port (default: 8888)
- `--components`: Components to enable (default: all)
