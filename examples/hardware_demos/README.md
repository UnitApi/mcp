# Hardware Demonstration Examples

This directory contains various hardware integration demonstrations using the UnitMCP library.

## Examples

### sensor_demo.py

This example demonstrates how to interface with various sensors.

**Features:**
- Temperature sensor reading
- Motion detection
- Light level sensing
- Data logging

### actuator_demo.py

This example demonstrates how to control various actuators.

**Features:**
- Servo motor control
- Relay switching
- LED control
- Motor driver integration

### led_control.py

This example demonstrates basic LED control functionality using the UnitMCP library.

**Features:**
- Simple LED blinking
- Different blink patterns
- Environment variable configuration
- Error handling

### traffic_light.py

This example demonstrates a traffic light simulation system.

**Features:**
- Traffic light simulation
- Pedestrian crossing system
- LED sequencing
- Environment variable configuration
- Error handling

## Environment Variables

All examples in this directory support configuration via environment variables. You can:

1. Create a `.env` file in this directory (copy from `txt.env` as a starting point)
2. Set environment variables in your shell before running the examples
3. Pass configuration via command-line arguments (where supported)

### Common Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RPI_HOST` | Hostname or IP address of the MCP server | localhost |
| `RPI_PORT` | Port number of the MCP server | 8080 |
| `SIMULATION_MODE` | Run in simulation mode without hardware | false |

### LED Control Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LED_PIN` | GPIO pin for the LED | 17 |
| `LED_ID` | Identifier for the LED | led1 |
| `BLINK_COUNT` | Number of times to blink | 5 |
| `BLINK_DURATION` | Duration of each blink in seconds | 0.5 |
| `FAST_BLINK` | Duration for fast blinking in seconds | 0.1 |
| `SLOW_BLINK` | Duration for slow blinking in seconds | 0.5 |
| `PATTERN_DURATION` | Duration to run each pattern in seconds | 3.0 |

### Traffic Light Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RED_LED_PIN` | GPIO pin for red light | 17 |
| `YELLOW_LED_PIN` | GPIO pin for yellow light | 27 |
| `GREEN_LED_PIN` | GPIO pin for green light | 22 |
| `RED_LIGHT_TIME` | Duration for red light in seconds | 5.0 |
| `YELLOW_LIGHT_TIME` | Duration for yellow light in seconds | 2.0 |
| `GREEN_LIGHT_TIME` | Duration for green light in seconds | 5.0 |

### Pedestrian Crossing Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CAR_RED_PIN` | GPIO pin for car red light | 17 |
| `CAR_GREEN_PIN` | GPIO pin for car green light | 22 |
| `PED_RED_PIN` | GPIO pin for pedestrian red light | 23 |
| `PED_GREEN_PIN` | GPIO pin for pedestrian green light | 24 |
| `BUTTON_PIN` | GPIO pin for pedestrian button | 25 |
| `CROSSING_TIME` | Duration for pedestrian crossing in seconds | 10.0 |
| `TRANSITION_TIME` | Duration for light transitions in seconds | 3.0 |
| `FLASH_COUNT` | Number of times to flash pedestrian green light | 3 |

## Usage

```bash
# Run with default settings (uses .env file if present)
python sensor_demo.py
python actuator_demo.py
python led_control.py
python traffic_light.py

# Run with specific environment variables
LED_PIN=18 BLINK_COUNT=10 python led_control.py
```

## Requirements

- UnitMCP library: `pip install -e ..`
- Appropriate hardware (LEDs, buttons, etc.) or simulation mode enabled
