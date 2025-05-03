# UnitMCP AI Examples

This directory contains examples demonstrating how to use the UnitMCP AI capabilities in various scenarios.

## Overview

UnitMCP provides a comprehensive AI infrastructure that includes:

- **Language Models (LLMs)**: Integration with Ollama, Claude, and OpenAI models
- **Speech Processing**: Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities
- **Natural Language Processing (NLP)**: Text analysis, entity extraction, and sentiment analysis
- **Computer Vision**: Image processing, object detection, and face analysis

## Examples

1. **[AI Demo](ai_demo.py)**: Basic demonstration of all AI capabilities
2. **[Voice Assistant](voice_assistant/)**: A complete voice assistant example with client and server components
3. **[Object Recognition](object_recognition/)**: Computer vision example for recognizing objects
4. **[Smart Home Control](smart_home/)**: Using LLMs to control smart home devices

## Getting Started

### Prerequisites

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up the necessary environment variables (if using cloud-based models):

```bash
export ANTHROPIC_API_KEY=your_claude_api_key
export OPENAI_API_KEY=your_openai_api_key
export GOOGLE_API_KEY=your_google_api_key
```

3. For Ollama, ensure the Ollama server is running:

```bash
ollama serve
```

### Running the Examples

Each example directory contains:

- `README.md`: Detailed instructions for the specific example
- `runner.py`: Main script to run the complete example
- `client.py`: Client-side implementation
- `server.py`: Server-side implementation
- `config/`: Configuration files for the example

To run an example:

```bash
cd examples/ai/voice_assistant
python runner.py
```

## Configuration

All AI components can be configured using YAML files in the `configs/yaml/ai/` directory:

- `config.yaml`: Main configuration file
- `llm.yaml`: Language model configurations
- `speech.yaml`: Speech processing configurations
- `nlp.yaml`: Natural language processing configurations
- `vision.yaml`: Computer vision configurations

## Additional Resources

- [UnitMCP Documentation](https://unitmcp.readthedocs.io/)
- [AI Module API Reference](https://unitmcp.readthedocs.io/en/latest/api/ai.html)
- [Configuration Guide](https://unitmcp.readthedocs.io/en/latest/guides/configuration.html)
