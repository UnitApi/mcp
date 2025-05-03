# UnitMCP Example: Hardware Demos

## Purpose

These examples demonstrate how to control various hardware devices using the UnitMCP library. They provide practical demonstrations of LED control and traffic light simulation, showing proper error handling and configuration through environment variables.

## Requirements

- Python 3.7+
- UnitMCP library (installed or in PYTHONPATH)
- Raspberry Pi or compatible hardware (optional, can run in simulation mode)

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

## How to Run

```bash
# Run LED control demo
python led_control.py

# Run traffic light demo
python traffic_light.py
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
