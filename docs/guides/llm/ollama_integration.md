# Ollama Integration Guide

This guide explains how to use Ollama with UnitMCP for natural language hardware control.

## Overview

UnitMCP integrates with Ollama to provide natural language processing capabilities for hardware control. This integration allows you to use Ollama's language models to interpret natural language commands and convert them into hardware actions.

## Installation

### Install Ollama

First, you need to install Ollama on your system. Follow the instructions on the [Ollama website](https://ollama.ai/download).

### Install UnitMCP

Make sure you have UnitMCP installed:

```bash
pip install unitmcp
```

## Configuration

### Environment Variables

Configure the Ollama integration using environment variables:

```bash
# Ollama configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama2

# Enable Ollama integration
ENABLE_OLLAMA=1
```

### Configuration File

You can also configure the Ollama integration using a YAML configuration file:

```yaml
ollama:
  host: localhost
  port: 11434
  model: llama2
  enabled: true
```

## Usage

### Basic Usage

```python
import asyncio
from unitmcp.llm.ollama import OllamaIntegration
from unitmcp.hardware.client import MCPHardwareClient

async def main():
    # Initialize the Ollama integration
    ollama = OllamaIntegration()
    
    # Initialize the hardware client
    client = MCPHardwareClient()
    await client.connect()
    
    # Process a natural language command
    command = "Turn on the LED on pin 17"
    
    # Parse the command using Ollama
    parsed_command = await ollama.parse_command(command)
    
    # Execute the parsed command
    result = await client.execute_command(
        parsed_command["device_type"],
        parsed_command["action"],
        parsed_command["parameters"]
    )
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Using with Docker

If you're using Docker, you can use the provided Docker Compose configuration:

```yaml
version: '3'
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    
  hardware-client:
    build:
      context: .
      dockerfile: docker/client/Dockerfile
    environment:
      - OLLAMA_HOST=ollama
      - OLLAMA_PORT=11434
      - OLLAMA_MODEL=llama2
      - ENABLE_OLLAMA=1
    depends_on:
      - ollama

volumes:
  ollama_data:
```

## Supported Models

The Ollama integration supports various language models, including:

- llama2
- codellama
- mistral
- vicuna
- orca-mini

To use a different model, set the `OLLAMA_MODEL` environment variable or update the configuration file.

## Customizing Prompts

You can customize the prompts used for natural language processing by creating a prompt template file:

```yaml
# prompts/hardware_control.yaml
system: |
  You are a helpful assistant that translates natural language commands into hardware control actions.
  
  Available devices:
  - LED (actions: on, off, blink)
  - Button (actions: press, release)
  - Display (actions: show, clear)
  
  Output format:
  {
    "device_type": "led",
    "action": "on",
    "parameters": {}
  }

user: |
  Translate the following command into a hardware action: "{{command}}"
```

Then load the prompt template in your code:

```python
ollama = OllamaIntegration(prompt_template_path="prompts/hardware_control.yaml")
```

## Troubleshooting

If you encounter issues with the Ollama integration, check the following:

1. Ensure Ollama is running: `curl http://localhost:11434/api/tags`
2. Check that the model is available: `ollama list`
3. Verify the environment variables are set correctly
4. Check the logs for error messages

For more help, see the [Troubleshooting Guide](../troubleshooting/README.md).
