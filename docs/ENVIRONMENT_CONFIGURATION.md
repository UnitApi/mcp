# UnitMCP Environment Configuration Guide

This document explains how to configure UnitMCP examples using environment variables, `.env` files, and YAML configuration files.

## Table of Contents

1. [Introduction](#introduction)
2. [Using .env Files](#using-env-files)
3. [Environment Variables Reference](#environment-variables-reference)
4. [YAML Configuration](#yaml-configuration)
5. [Configuration Precedence](#configuration-precedence)
6. [Simulation vs. Real Hardware](#simulation-vs-real-hardware)
7. [Examples](#examples)

## Introduction

UnitMCP provides multiple ways to configure your applications:

- **Environment Variables**: Quick, simple configuration for individual runs
- **.env Files**: Persistent configuration stored in a file
- **YAML Configuration**: More complex, structured configuration

Each approach has its advantages, and you can use them together based on your needs.

## Using .env Files

### What is a .env File?

A `.env` file is a simple text file containing key-value pairs that define environment variables:

```
KEY1=value1
KEY2=value2
# This is a comment
KEY3="value with spaces"
```

### How to Use .env Files in UnitMCP

1. **Create a .env file**: Each example directory includes an `.env.example` file that you can copy:

   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your preferred settings:

   ```bash
   nano .env
   ```

3. **Run your application**: The variables will be automatically loaded:

   ```bash
   python runner.py
   ```

### How .env Files Work in Code

UnitMCP uses the `python-dotenv` library to load environment variables from `.env` files. The code typically looks like this:

```python
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Access environment variables
server_host = os.getenv("SERVER_HOST", "localhost")
server_port = int(os.getenv("SERVER_PORT", "8080"))
simulation = os.getenv("SIMULATION", "0") == "1"
```

### .env File Format Rules

- Each line should be in the format `KEY=value`
- Lines starting with `#` are treated as comments
- Empty lines are ignored
- Values can be quoted or unquoted
- No spaces around the `=` sign (use `KEY=value`, not `KEY = value`)

## Environment Variables Reference

Here are the common environment variables used across UnitMCP examples:

### Server Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SERVER_HOST` | Hostname or IP address of the server | localhost | 192.168.1.2 |
| `SERVER_PORT` | Port number of the server | 8080 | 8888 |
| `LOG_LEVEL` | Logging level | INFO | DEBUG |

### Hardware Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SIMULATION` | Run in simulation mode (1=yes, 0=no) | 0 | 1 |
| `GPIO_PINS` | Comma-separated list of GPIO pins to use | 17,18,27 | 18,23,24 |
| `LED_PINS` | Comma-separated list of LED pins | 17,22 | 18 |
| `BUTTON_PIN` | GPIO pin for button input | 23 | 27 |

### Connection Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RPI_HOST` | Hostname or IP address of Raspberry Pi | localhost | 192.168.1.2 |
| `RPI_PORT` | SSH or TCP port for Raspberry Pi | 22 | 8888 |
| `RPI_USERNAME` | Username for SSH connection to Raspberry Pi | pi | username |
| `SSH_KEY_PATH` | Path to SSH key file | ~/.ssh/id_rsa | /path/to/key.pem |

### Audio Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `AUDIO_DEVICE` | Audio device to use | default | hw:0,0 |
| `SAMPLE_RATE` | Audio sample rate | 44100 | 16000 |
| `CHANNELS` | Number of audio channels | 1 | 2 |

### LLM Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LLM_PROVIDER` | LLM provider to use | openai | ollama |
| `LLM_MODEL` | Model name | gpt-3.5-turbo | llama2 |
| `OPENAI_API_KEY` | OpenAI API key | - | sk-... |
| `TEMPERATURE` | Model temperature | 0.7 | 0.5 |

## YAML Configuration

For more complex configurations, UnitMCP supports YAML files. These provide a structured way to organize configuration parameters.

### Basic YAML Structure

```yaml
# server.yaml
server:
  host: 0.0.0.0
  port: 8080
  log_level: INFO
  
hardware:
  simulation: true
  gpio_pins: [17, 18, 27]
  led_pins: [17, 22]
```

### Loading YAML Configuration in Code

```python
import yaml
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Path to config file")
args = parser.parse_args()

# Load configuration from YAML file
config = {}
if args.config:
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

# Access configuration values
server_host = config.get("server", {}).get("host", "localhost")
server_port = config.get("server", {}).get("port", 8080)
simulation = config.get("hardware", {}).get("simulation", False)
```

### Example YAML Configurations

#### Server Configuration (server.yaml)

```yaml
server:
  host: 0.0.0.0
  port: 8080
  log_level: INFO
  max_connections: 100
  timeout: 30
  
hardware:
  simulation: true
  gpio_pins: [17, 18, 27]
  led_pins: [17, 22]
  
logging:
  file: server.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  rotate: true
  max_size: 10485760  # 10MB
```

#### Client Configuration (client.yaml)

```yaml
client:
  host: 192.168.1.2
  port: 8080
  timeout: 30
  reconnect: true
  reconnect_delay: 5
  
commands:
  aliases:
    led_on: "gpio 18 out 1"
    led_off: "gpio 18 out 0"
    blink: "led led1 blink 0.5 0.5"
    
ui:
  theme: dark
  font_size: 12
  show_status_bar: true
```

## Configuration Precedence

When multiple configuration methods are used, UnitMCP follows this precedence order:

1. **Command-line environment variables** (highest priority)
   ```bash
   SERVER_HOST=192.168.1.100 python runner.py
   ```

2. **.env file variables**
   ```
   # .env
   SERVER_HOST=192.168.1.100
   ```

3. **YAML configuration files**
   ```yaml
   # config.yaml
   server:
     host: 192.168.1.100
   ```

4. **Default values in code** (lowest priority)
   ```python
   server_host = os.getenv("SERVER_HOST", "localhost")
   ```

This means that if a variable is defined in multiple places, the value from the higher priority source will be used.

## Simulation vs. Real Hardware

UnitMCP allows you to easily switch between simulation mode and real hardware by changing the `SIMULATION` environment variable.

### Simulation Mode (SIMULATION=1)

Simulation mode allows you to test your code without physical hardware:

```bash
# Via .env file
SIMULATION=1

# Via command line
SIMULATION=1 python runner.py

# Via YAML
hardware:
  simulation: true
```

In simulation mode:
- GPIO operations are simulated in memory
- Hardware interactions are logged but not actually performed
- You can test your code on any computer without physical hardware

### Real Hardware Mode (SIMULATION=0)

To control real hardware (like a Raspberry Pi):

```bash
# Via .env file
SIMULATION=0

# Via command line
SIMULATION=0 python runner.py

# Via YAML
hardware:
  simulation: false
```

When using real hardware:
- Make sure to set the correct `SERVER_HOST` to your device's IP address
- Ensure you have the proper permissions to access GPIO pins
- Connect the physical hardware according to your pin configuration

## Examples

### Basic Example with .env File

1. Create a `.env` file:

   ```
   # Server configuration
   SERVER_HOST=localhost
   SERVER_PORT=8080
   LOG_LEVEL=INFO
   
   # Hardware configuration
   SIMULATION=1
   GPIO_PINS=17,18,27
   LED_PINS=17,22
   ```

2. Run your application:

   ```bash
   python runner.py
   ```

### Connecting to a Raspberry Pi

1. Create a `.env` file:

   ```
   # Server configuration
   SERVER_HOST=192.168.1.2  # IP address of your Raspberry Pi
   SERVER_PORT=8080
   LOG_LEVEL=INFO
   
   # Connection configuration
   RPI_USERNAME=pi  # Username for SSH connection
   SSH_KEY_PATH=~/.ssh/id_rsa  # Optional: path to SSH key
   
   # Hardware configuration
   SIMULATION=0
   GPIO_PINS=17,18,27
   LED_PINS=18
   ```

2. Run your application:

   ```bash
   python runner.py
   ```

   Or connect via SSH:

   ```bash
   python simple_remote_shell.py --ssh
   ```

   The application will use the RPI_USERNAME from the .env file.

### Using Both .env and YAML

1. Create a `.env` file for basic settings:

   ```
   SERVER_HOST=192.168.1.2
   SERVER_PORT=8080
   SIMULATION=0
   ```

2. Create a `config.yaml` file for more complex settings:

   ```yaml
   hardware:
     gpio_pins: [17, 18, 27]
     led_pins: [18]
     button_pin: 23
     
   logging:
     file: app.log
     level: INFO
     format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
   ```

3. Run your application with both:

   ```bash
   python runner.py --config config.yaml
   ```

### Overriding Settings for a Single Run

If you have a `.env` file but want to override some settings for a single run:

```bash
SERVER_HOST=192.168.1.100 LOG_LEVEL=DEBUG python runner.py
```

This will use all the settings from your `.env` file except for `SERVER_HOST` and `LOG_LEVEL`, which will be taken from the command line.

## Troubleshooting

### Common Issues

1. **Environment variables not being loaded**
   - Make sure your `.env` file is in the correct directory
   - Check that you're calling `load_dotenv()` in your code
   - Verify the file format (no spaces around `=`, etc.)

2. **YAML configuration not being applied**
   - Check that the YAML file has the correct structure
   - Verify that you're passing the correct path to the file
   - Look for syntax errors in the YAML file

3. **Precedence issues**
   - Remember that command-line variables override `.env` variables
   - Check all possible sources if a setting isn't being applied as expected

### Debugging Configuration

To debug your configuration, you can print the loaded values:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Print all environment variables
for key, value in os.environ.items():
    if key.startswith("SERVER_") or key in ["SIMULATION", "LOG_LEVEL"]:
        print(f"{key}={value}")
```

Or add a debug flag to your application:

```bash
DEBUG=1 python runner.py
```

And check for it in your code:

```python
if os.getenv("DEBUG") == "1":
    print("Configuration loaded:")
    print(f"SERVER_HOST: {server_host}")
    print(f"SERVER_PORT: {server_port}")
    print(f"SIMULATION: {simulation}")
