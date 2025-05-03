# UnitMCP Example: Hardware Demos

## Purpose

These examples demonstrate how to control various hardware devices using the UnitMCP library. They provide practical demonstrations of LED control and traffic light simulation, showing proper error handling and configuration through environment variables.

## Requirements

- Python 3.7+
- UnitMCP library (installed or in PYTHONPATH)
- Raspberry Pi or compatible hardware (optional, can run in simulation mode)

## Files in This Directory

- `led_control.py` - Demo for controlling LEDs (blinking, patterns)
- `traffic_light.py` - Traffic light simulation with configurable timing
- `runner.py` - Unified runner script to manage both client and server components
- `server.py` - Server implementation for handling hardware requests
- `client.py` - Client implementation for connecting to the server
- `config/` - Directory containing configuration files:
  - `client.yaml` - Client configuration settings
  - `server.yaml` - Server configuration settings

## Environment Variables

These examples use the following environment variables which can be configured in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `RPI_HOST` | Hostname or IP address of the Raspberry Pi | `localhost` |
| `RPI_PORT` | Port number for the MCP server | `8080` |
| `LED_PIN` | GPIO pin number for the LED | `17` |
| `LED_ID` | Identifier for the LED device | `led1` |
| `BLINK_COUNT` | Number of times to blink the LED | `5` |
| `BLINK_DURATION` | Duration of each blink in seconds | `0.5` |
| `RED_LED_PIN` | GPIO pin for red traffic light | `17` |
| `YELLOW_LED_PIN` | GPIO pin for yellow traffic light | `27` |
| `GREEN_LED_PIN` | GPIO pin for green traffic light | `22` |
| `SIMULATION_MODE` | Run in simulation mode without hardware | `false` |

## Using the Runner

The `runner.py` script provides a standardized way to start and manage both client and server components:

```bash
# Run both client and server with default configuration
python runner.py

# Run only the server
python runner.py --server-only

# Run only the client with LED control demo
python runner.py --client-only --demo led

# Run only the client with traffic light demo
python runner.py --client-only --demo traffic

# Specify custom configuration files
python runner.py --server-config config/custom_server.yaml --client-config config/custom_client.yaml

# Enable verbose logging
python runner.py --verbose
```

### Environment Configuration

The runner and example scripts can be configured using:

1. **Environment Variables (.env file)**: Create a `.env` file in the example directory with configuration values:

```
# Server configuration
RPI_HOST=192.168.1.100
RPI_PORT=8080
LOG_LEVEL=INFO

# Hardware configuration
LED_PIN=17
LED_ID=led1
BLINK_COUNT=10
BLINK_DURATION=0.2
RED_LED_PIN=17
YELLOW_LED_PIN=27
GREEN_LED_PIN=22
SIMULATION_MODE=true
```

2. **Command Line Arguments**: Pass configuration values directly to the runner:

```bash
# Configure server host and port
RPI_HOST=192.168.1.100 RPI_PORT=8888 python runner.py

# Enable simulation mode
SIMULATION_MODE=true python runner.py

# Configure LED parameters
LED_PIN=18 LED_ID=demo_led BLINK_COUNT=3 python runner.py --client-only --demo led
```

3. **Configuration Files**: Specify custom YAML configuration files:

```bash
python runner.py --server-config config/custom_server.yaml
```

The configuration precedence is: Command Line > .env File > Default Configuration Files

## How to Run

```bash
# Run LED control demo
python led_control.py

# Run traffic light demo
python traffic_light.py

# Or use the runner for a more standardized approach
python runner.py --demo led
python runner.py --demo traffic
```

## Example Output

### LED Control Demo
```
LED Control Demo
1. Simple blink
2. LED patterns
Select demo (1-2): 1
Connecting to MCP server at localhost:8080
Using LED on pin 17 with ID 'led1'
LED setup complete
Blink 1
Blink 2
Blink 3
Blink 4
Blink 5
LED blinking complete
```

### Traffic Light Demo
```
Connecting to MCP server at localhost:8080
Using LED pins: Red=17, Yellow=27, Green=22
Timing: Red=5.0s, Yellow=2.0s, Green=5.0s
Setting up traffic light system...
Traffic light running (Ctrl+C to stop)
RED
RED + YELLOW
GREEN
YELLOW
...
```

## Additional Notes

- These examples can be run in simulation mode by setting the `SIMULATION_MODE` environment variable to `true`.
- For real hardware control, ensure that the UnitMCP server is running on the target device.
- The traffic light example includes a pedestrian crossing simulation that can be selected when running the script.
