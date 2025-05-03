# UnitMCP Example: Integrated Demo

## Purpose

This example demonstrates the integration of various UnitMCP features including:
- Pipeline execution for automated hardware control
- Shell command interface for interactive control
- Hardware management through a unified API
- Error handling and recovery mechanisms

It serves as a showcase example that demonstrates best practices for building complex applications with UnitMCP.

## Requirements

- Python 3.7+
- UnitMCP library (installed or in PYTHONPATH)
- Netcat (`nc`) for the interactive shell script
- Hardware devices (optional, can run in simulation mode)

## Environment Variables

This example uses the following environment variables which can be configured in a `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `RPI_HOST` | Hostname or IP address of the Raspberry Pi | `localhost` |
| `RPI_PORT` | Port number for the MCP server | `8080` |
| `LED_PIN` | GPIO pin number for the LED | `17` |
| `FAST_BLINK` | Duration for fast blinking in seconds | `0.1` |
| `SLOW_BLINK` | Duration for slow blinking in seconds | `0.5` |
| `SIMULATION_MODE` | Run in simulation mode without hardware | `false` |

## How to Run

```bash
# Run the integrated demo
python integrated_demo.py

# After running the demo, you can also try the generated shell script
./interactive_demo.sh
```

## Example Output

```
UnitMCP Integrated Demo
======================

This demo showcases the integration of various UnitMCP features:
1. Pipeline execution
2. Shell command interface
3. Hardware control
4. Automation capabilities

Created interactive shell script: interactive_demo.sh

MCP Hardware Integrated Demo
==================================================

1. Executing LED control pipeline...
LED pipeline result: True

2. Demonstrating shell commands...
mcp> status
MCP Hardware Shell - Connected: False
mcp> set led_pin 17
Variable led_pin set to 17
mcp> get led_pin
led_pin = 17
mcp> pipeline_list
Available pipelines:
- led_control: Comprehensive LED control demonstration
- automation: Automation pipeline with error handling
mcp> vars
Variables:
led_pin = 17

3. Creating and running a custom pipeline through shell...
mcp> pipeline_create custom_demo
Created pipeline: custom_demo
mcp> pipeline_add custom_demo type Hello from custom pipeline!
Added step to pipeline custom_demo
mcp> pipeline_add custom_demo move 100 100
Added step to pipeline custom_demo
mcp> pipeline_add custom_demo click left
Added step to pipeline custom_demo
mcp> pipeline_run custom_demo
Running pipeline: custom_demo
Pipeline completed with success: True

4. Saving pipelines...
Pipelines saved to integrated_demo_pipelines

Demo completed successfully!

You can also try the interactive shell script:
  ./interactive_demo.sh

Thank you for exploring UnitMCP!
```

## Additional Notes

- The demo creates a pipeline manager that can save and load pipeline configurations
- The interactive shell script demonstrates how to control hardware from bash scripts
- Pipeline configurations are saved to the `integrated_demo_pipelines` directory
- This example demonstrates proper error handling and recovery mechanisms
