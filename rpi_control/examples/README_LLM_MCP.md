# LLM Hardware Control with MCP

This directory contains examples of using Large Language Models (LLMs) to control hardware through the Model Context Protocol (MCP).

## Overview

The integration allows you to:

1. Create an MCP server that exposes hardware control capabilities as tools
2. Connect an LLM to the MCP server to control hardware through natural language
3. Use the existing Raspberry Pi hardware control infrastructure

## Files

- `llm_hardware_control.py`: MCP server that exposes hardware control tools
- `llm_hardware_client.py`: Client that connects to the MCP server and an LLM

## Prerequisites

1. A Raspberry Pi with the UnitMCP hardware control server running
2. Python 3.7+ with the required dependencies
3. An API key for an LLM service (e.g., OpenAI)

## Installation

1. Install the required dependencies:

```bash
pip install -r ../requirements.txt
```

2. Set up your environment variables:

```bash
# Copy the sample environment file
cp ../env.sample ../.env

# Edit the .env file with your configuration
nano ../.env
```

Make sure to set the following variables in your `.env` file:

```
RPI_HOST=your_raspberry_pi_hostname_or_ip
RPI_PORT=8080
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Starting the MCP Server

Run the MCP server that exposes hardware control tools:

```bash
python llm_hardware_control.py
```

Options:
- `--host`: Raspberry Pi hostname or IP address (default: from .env)
- `--port`: Raspberry Pi port (default: from .env)
- `--server-name`: Name of the MCP server (default: "Hardware Control")

### Using the LLM Client

Run the LLM client to control hardware through natural language:

```bash
python llm_hardware_client.py
```

Options:
- `--server-command`: Command to start the MCP server (default: python)
- `--server-args`: Arguments for the server command (default: rpi_control/examples/llm_hardware_control.py)
- `--api-key`: API key for the LLM service (default: from OPENAI_API_KEY env var)
- `--model`: LLM model to use (default: gpt-3.5-turbo)

## Example Conversation

Once the client is running, you can control hardware through natural language:

```
You: Turn on the LED on pin 17
Assistant: I'll turn on the LED on pin 17 for you.

{
  "tool": "control_led",
  "arguments": {
    "pin": 17,
    "state": "on"
  }
}

Tool execution result: {'success': True, 'message': 'LED on pin 17 turned on'}
