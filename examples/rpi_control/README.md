# UnitMCP Example: Raspberry Pi Control

## Purpose

This example demonstrates how to control Raspberry Pi hardware using the UnitMCP library. It showcases:

- Connecting to a Raspberry Pi running the UnitMCP server
- Controlling GPIO devices like LEDs, buttons, and traffic lights
- Loading configuration from YAML files
- Running automated hardware demos
- Implementing proper error handling and resource management

This example serves as a reference implementation for building Raspberry Pi-based hardware control applications with UnitMCP.

## Requirements

- Python 3.7+
- UnitMCP library (installed or in PYTHONPATH)
- Raspberry Pi with GPIO pins (or simulation mode)
- PyYAML (`pip install pyyaml`)
- Hardware components (optional):
  - LEDs
  - Push buttons
  - Resistors (220Ω for LEDs, 10kΩ for buttons)
  - Jumper wires

## Environment Variables

This example uses the following environment variables which can be configured in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `RPI_HOST` | Hostname or IP address of the Raspberry Pi | `localhost` |
| `RPI_PORT` | Port number for the MCP server | `8080` |
| `LED_PIN` | GPIO pin number for the LED | `17` |
| `BUTTON_PIN` | GPIO pin number for the button | `27` |
| `RED_PIN` | GPIO pin for red traffic light | `17` |
| `YELLOW_PIN` | GPIO pin for yellow traffic light | `27` |
| `GREEN_PIN` | GPIO pin for green traffic light | `22` |
| `FAST_BLINK` | Duration for fast blinking in seconds | `0.1` |
| `SLOW_BLINK` | Duration for slow blinking in seconds | `0.5` |
| `SIMULATION_MODE` | Run in simulation mode without hardware | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

## How to Run

```bash
# Run the hardware client with LED demo
python hardware_client.py --demo led

# Run the hardware client with button demo
python hardware_client.py --demo button

# Run the hardware client with traffic light demo
python hardware_client.py --demo traffic_light

# Run with custom host and port
python hardware_client.py --host 192.168.1.100 --port 8888

# Run the configuration automation example
python config_automation_example.py --config my_custom_config.yaml

# Run all examples in sequence
./run_examples.sh
```

## Example Output

### LED Demo

```
UnitMCP Raspberry Pi Hardware Client Example
===========================================
Running led demo...
2025-05-03 09:46:17,123 - RPiHardwareClient - INFO - Connecting to MCP server at localhost:8080
2025-05-03 09:46:17,234 - RPiHardwareClient - INFO - Connected to MCP server successfully
2025-05-03 09:46:17,345 - RPiHardwareClient - INFO - Running led demo
2025-05-03 09:46:17,456 - RPiHardwareClient - INFO - Setting up LED demo_led on pin 17
2025-05-03 09:46:17,567 - RPiHardwareClient - INFO - LED demo_led setup successful
2025-05-03 09:46:17,678 - RPiHardwareClient - INFO - Turning LED on
2025-05-03 09:46:17,789 - RPiHardwareClient - INFO - LED demo_led control successful
2025-05-03 09:46:18,901 - RPiHardwareClient - INFO - Blinking LED fast
2025-05-03 09:46:19,012 - RPiHardwareClient - INFO - LED demo_led control successful
2025-05-03 09:46:21,123 - RPiHardwareClient - INFO - Blinking LED slow
2025-05-03 09:46:21,234 - RPiHardwareClient - INFO - LED demo_led control successful
2025-05-03 09:46:24,345 - RPiHardwareClient - INFO - Turning LED off
2025-05-03 09:46:24,456 - RPiHardwareClient - INFO - LED demo_led control successful
Demo completed successfully: LED demo completed successfully
Disconnected from MCP server
```

### Configuration Automation

```
UnitMCP Configuration Automation Example
=======================================
Loading configuration from my_custom_config.yaml
Configuration loaded successfully
Connecting to MCP server at localhost:8080
Connected to MCP server
Setting up devices from configuration...
Setting up LED main_led on pin 17
Setting up button user_button on pin 27
Setting up traffic light traffic1 with pins 17, 27, 22
All devices set up successfully
Running automation sequence...
Step 1: Turn on main_led - Success
Step 2: Wait for button press - Waiting...
Button pressed! Continuing...
Step 3: Traffic light cycle - Success
Automation completed successfully
Disconnected from MCP server
```

## Additional Notes

- The `hardware_client.py` file provides a reusable client class for controlling Raspberry Pi hardware
- The `config_automation_example.py` demonstrates how to load device configurations from YAML files
- The `run_examples.sh` script shows how to run multiple examples in sequence
- All examples include proper error handling and resource cleanup
- The code is designed to be easily extended with additional hardware devices and control patterns
