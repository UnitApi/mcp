# Ollama Integration Examples

This directory contains examples demonstrating integration with Ollama LLM for the MCP Hardware Project.

## Examples

### ollama_integration.py

This example shows how to integrate Ollama large language models with MCP hardware control, allowing natural language processing to control hardware devices.

**Features:**
- Connect to Ollama LLM service
- Process natural language commands
- Convert language commands to hardware control actions
- Provide feedback through the LLM

**Usage:**
```bash
python ollama_integration.py
```

**Requirements:**
- Ollama installed and running
- MCP hardware package with ollama extras: `pip install -e ".[ollama]"`