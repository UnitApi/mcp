# UnitMCP LLM Integration Examples

This directory contains examples demonstrating how to integrate Large Language Models (LLMs) with the UnitMCP hardware control framework.

## Available Examples

### Claude Plugin Demo

The `claude_plugin_demo.py` demonstrates how to use the Claude UnitMCP Plugin for natural language hardware control:

```bash
# Run the Claude plugin demo
python claude_plugin_demo.py

# Run with verbose logging
python claude_plugin_demo.py --verbose
```

This example shows how to:
- Connect to Claude API for natural language processing
- Parse hardware commands from natural language
- Execute hardware control actions based on language input
- Handle ambiguous or unclear instructions
- Provide feedback and confirmation in natural language

### Ollama Integration

The `ollama_integration.py` demonstrates how to integrate locally-hosted LLMs using Ollama:

```bash
# Run the Ollama integration example
python ollama_integration.py

# Specify a different model
python ollama_integration.py --model llama3:8b
```

This example showcases:
- Setting up a connection to a local Ollama instance
- Using different models for hardware control
- Processing hardware commands with reduced latency
- Handling offline operation without internet connectivity
- Fine-tuning models for hardware-specific terminology

## Key Features

### 1. Natural Language Command Processing

The examples demonstrate how to process natural language commands for hardware control:

```python
# Example natural language processing
response = llm_client.process("Turn on the red LED and make it blink slowly")

# Extract structured commands
commands = command_parser.parse(response)

# Execute the commands
for cmd in commands:
    hardware_client.execute(cmd)
```

### 2. Context-Aware Interactions

The examples show how to maintain context across multiple interactions:

```python
# Initialize conversation context
context = ConversationContext()

# First interaction
context.add_user_message("Connect to my Raspberry Pi")
response = llm_client.process_with_context(context)
context.add_assistant_message(response)

# Second interaction with context
context.add_user_message("Turn on the LED connected to pin 17")
response = llm_client.process_with_context(context)
```

### 3. Hardware Abstraction

The examples demonstrate how LLMs can work with hardware abstractions:

```python
# Define hardware abstractions
devices = {
    "living_room_light": {"type": "led", "pin": 17},
    "kitchen_light": {"type": "led", "pin": 18},
    "front_door": {"type": "sensor", "pin": 27}
}

# Process natural language with hardware context
response = llm_client.process("Turn on the living room light", 
                             hardware_context=devices)
```

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- For Claude integration: Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- For Ollama integration: Ollama installed and running locally

For Claude integration:
```bash
export ANTHROPIC_API_KEY=your_api_key_here
python claude_plugin_demo.py
```

For Ollama integration:
```bash
# Start Ollama server (in a separate terminal)
ollama serve

# Run the example
python ollama_integration.py
```

## Configuration

The LLM examples can be configured using YAML files in the `config/` directory:

- `claude.yaml`: Configuration for Claude API integration
- `ollama.yaml`: Configuration for Ollama integration
- `prompts.yaml`: Template prompts for different scenarios

## Security Considerations

When using LLMs for hardware control, consider these security practices:

1. **Command Validation**: Always validate commands before execution
2. **Restricted Access**: Limit which hardware can be controlled
3. **Confirmation**: Require confirmation for potentially dangerous operations
4. **Monitoring**: Log all commands and actions for review
5. **Fallbacks**: Implement safe fallback behaviors for unclear instructions

## Additional Resources

- [Claude API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [UnitMCP LLM Integration Guide](../../docs/integrations/llm_integration.md)
