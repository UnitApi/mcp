# UnitMCP Runner

UnitMCP Runner is a comprehensive service that configures and runs both client and server environments based on YAML configuration, allowing for remote hardware control through LLM integration (Ollama or Claude).

## Features

- **Unified Configuration**: Configure both server and client from a single YAML file
- **LLM Integration**: Control hardware using natural language through Ollama or Claude
- **Remote Server Support**: Connect to remote UnitMCP servers via SSH
- **Interactive Mode**: Issue commands and receive responses in real-time
- **Simulation Mode**: Test your setup without physical hardware
- **Raspberry Pi Optimization**: Automatic performance optimization for Raspberry Pi
- **Git Repository Integration**: Clone, configure, and run applications directly from Git repositories

## Directory Structure

```
UnitMCP Runner
├── src/unitmcp/runner/           # Core implementation
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # Main runner implementation
│   ├── server_setup.py           # Server configuration
│   ├── client_setup.py           # Client configuration
│   ├── llm_interface.py          # Abstract LLM interface
│   ├── ollama_interface.py       # Ollama integration
│   └── claude_interface.py       # Claude integration
├── configs/yaml/runner/          # Configuration files
│   ├── default_runner.yaml       # Default configuration
│   ├── led_control.yaml          # LED-specific configuration
│   └── claude_runner.yaml        # Claude integration configuration
└── examples/runner/              # Example implementations
    ├── runner.py                 # Command-line runner
    ├── git_runner.py             # Git repository runner
    ├── git_runner_integration.py # Git runner with UnitMCP integration
    ├── README_GIT_RUNNER.md      # Git runner documentation
    ├── tests/                    # Test cases
    └── docs/                     # Documentation
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- UnitMCP installed
- For Ollama integration: Ollama installed and running
- For Claude integration: Anthropic API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/UnitApi.git
   cd UnitApi/mcp
   ```

2. Install the dependencies:
   ```
   pip install -e .
   ```

3. Set up environment variables (for Claude integration):
   ```
   export ANTHROPIC_API_KEY=your_api_key
   ```

### Usage

Run with default configuration:
```
python examples/runner/runner.py
```

Specify a configuration file:
```
python examples/runner/runner.py --config configs/yaml/runner/led_control.yaml
```

Run in simulation mode:
```
python examples/runner/runner.py --simulation
```

Run in interactive mode:
```
python examples/runner/runner.py --interactive
```

Run only the server or client:
```
python examples/runner/runner.py --mode server
python examples/runner/runner.py --mode client
```

### Configuration

UnitMCP Runner uses YAML configuration files to define the server, client, and LLM settings. Example:

```yaml
# Server configuration
server:
  enabled: true
  host: localhost
  port: 8888
  simulation: false

# Client configuration
client:
  enabled: true
  server_host: localhost
  server_port: 8888
  devices:
    led1:
      type: led
      pin: 17
      name: Status LED

# LLM configuration
llm:
  enabled: true
  type: ollama
  model: llama3
  host: localhost
  port: 11434

# Runner configuration
runner:
  interactive: true
  log_level: info
```

## Examples

### Control an LED using natural language

1. Start the runner with the LED configuration:
   ```
   python examples/runner/runner.py --config configs/yaml/runner/led_control.yaml --interactive
   ```

2. Enter natural language commands:
   ```
   > Turn on the red LED
   > Make the blue LED blink
   > Turn off all LEDs
   ```

### Using Claude for more advanced control

1. Set your Anthropic API key:
   ```
   export ANTHROPIC_API_KEY=your_api_key
   ```

2. Start the runner with Claude configuration:
   ```
   python examples/runner/runner.py --config configs/yaml/runner/claude_runner.yaml --interactive
   ```

3. Enter complex commands:
   ```
   > Turn on the status LED and read the temperature
   > If the button is pressed, toggle the power relay
   ```

## Git Runner

UnitMCP Git Runner is an extension to the UnitMCP Runner that allows you to clone, configure, and run applications directly from Git repositories. It supports various application types including shell scripts, Node.js, Python, PHP, and static HTML.

### Git Runner Features

- **Automatic Application Type Detection**: Automatically detect the type of application in the repository
- **Dependency Installation**: Install dependencies for different application types
- **Environment Variable Configuration**: Configure environment variables from .env files or interactively
- **Intelligent Log Analysis**: Monitor logs and provide intelligent suggestions for troubleshooting
- **UnitMCP Integration**: Seamlessly integrate with UnitMCP for client-server applications
- **CI/CD System Detection**: Detect and use CI/CD configurations from GitHub, GitLab, etc.

### Git Runner Usage

Basic usage:
```
python examples/runner/git_runner.py https://github.com/username/repo.git
```

With UnitMCP integration:
```
python examples/runner/git_runner_integration.py https://github.com/username/repo.git
```

For more details, see [Git Runner Documentation](README_GIT_RUNNER.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
