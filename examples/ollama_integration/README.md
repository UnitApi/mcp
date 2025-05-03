# UnitMCP Example: Ollama Integration

## Purpose

This example demonstrates how to integrate Ollama language models with UnitMCP hardware control. It enables natural language processing for hardware control, allowing users to:

- Control hardware devices using natural language commands
- Create an AI agent that can interpret user intent and execute appropriate hardware actions
- Run in various modes including interactive, automated demo, and voice control

This integration showcases how to build AI-powered hardware control systems with UnitMCP.

## Requirements

- Python 3.7+
- UnitMCP library (installed or in PYTHONPATH)
- Ollama installed locally (https://ollama.ai/)
- For voice control mode:
  - SpeechRecognition (`pip install SpeechRecognition`)
  - gTTS (`pip install gTTS`)
  - pygame (`pip install pygame`)
- Hardware devices (optional, can run in simulation mode)

## Environment Variables

This example uses the following environment variables which can be configured in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `RPI_HOST` | Hostname or IP address of the Raspberry Pi | `localhost` |
| `RPI_PORT` | Port number for the MCP server | `8080` |
| `OLLAMA_MODEL` | Ollama model to use | `llama2` |
| `OLLAMA_SYSTEM_PROMPT` | System prompt for the Ollama model | *See code for default* |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SIMULATION_MODE` | Run in simulation mode without hardware | `false` |

## How to Run

The example can be run in several different modes:

```bash
# Run in interactive mode (default)
python ollama_integration.py --interactive

# Run the MCP server
python ollama_integration.py --server

# Run the automation demo
python ollama_integration.py --demo

# Run with voice control
python ollama_integration.py --voice

# Specify a different Ollama model
python ollama_integration.py --model llama2-uncensored

# Specify custom host and port
python ollama_integration.py --host 192.168.1.100 --port 8888
```

## Example Output

### Interactive Mode

```
Ollama Hardware Agent - Model: llama2
Type 'exit' or 'quit' to end the session
==================================================

Enter command: Set up an LED on pin 17 and call it demo_led

Processing...
Success: {
  "status": "success",
  "message": "LED setup on pin 17"
}

Enter command: Blink the demo_led with 0.2 second intervals

Processing...
Success: {
  "status": "success",
  "message": "LED blinking"
}

Enter command: Turn off the demo_led

Processing...
Success: {
  "status": "success",
  "message": "LED turned off"
}

Enter command: exit
```

### Automation Demo

```
Ollama Hardware Automation Demo
==================================================

Step 1: Set up an LED on pin 17 and call it main_led
Success: {
  "status": "success",
  "message": "LED setup on pin 17"
}

Step 2: Blink the main_led with 0.2 second intervals
Success: {
  "status": "success",
  "message": "LED blinking"
}

Step 3: Wait for 5 seconds then turn off the main_led
Success: {
  "status": "success",
  "message": "LED turned off"
}

Step 4: Move the mouse to position x=500, y=500
Success: {
  "status": "success",
  "message": "Mouse moved to (500, 500)"
}

Step 5: Take a screenshot
Success: {
  "status": "success",
  "message": "Screenshot taken",
  "path": "/tmp/mcp_screenshot_20230615123456.png"
}
```

## Additional Notes

- The Ollama integration uses a system prompt that defines available commands and expected response format
- The agent processes natural language commands and converts them to structured hardware commands
- Voice control mode requires additional dependencies and uses Google's speech recognition API
- The example includes error handling and graceful disconnection from the MCP server
- For production use, consider implementing more sophisticated error handling and recovery mechanisms