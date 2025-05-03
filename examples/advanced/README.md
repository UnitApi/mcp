# UnitMCP Advanced Examples

This directory contains advanced examples that demonstrate more complex usage patterns and integrations of the UnitMCP library.

## Available Examples

### Configuration Automation

The `config_automation_example.py` demonstrates how to automate hardware configuration and control using YAML configuration files:

```bash
# Run with default configuration
python config_automation_example.py

# Run with custom configuration
python config_automation_example.py --config config/custom_automation.yaml
```

This example shows how to:
- Load device configurations from YAML files
- Set up multiple devices with a single configuration
- Create automation sequences with conditional logic
- Handle errors and provide fallback behaviors
- Log automation progress and results

### Automation Example

The `automation_example.py` demonstrates how to create complex automation workflows:

```bash
# Run the automation example
python automation_example.py

# Run with simulation mode
SIMULATION=1 python automation_example.py
```

This example showcases:
- Event-driven automation with triggers and actions
- Scheduled tasks and recurring operations
- State machines for complex control logic
- Integration with external systems
- Parallel execution of multiple automation tasks

## Advanced Features

These examples demonstrate advanced UnitMCP features:

### 1. Pipeline Processing

The examples use the UnitMCP pipeline architecture to process commands and data:

```python
# Example pipeline definition
pipeline = [
    {"stage": "parse", "module": "unitmcp.pipeline.parsers", "function": "yaml_parser"},
    {"stage": "validate", "module": "unitmcp.pipeline.validators", "function": "schema_validator"},
    {"stage": "transform", "module": "unitmcp.pipeline.transformers", "function": "device_transformer"},
    {"stage": "execute", "module": "unitmcp.pipeline.executors", "function": "device_executor"}
]

# Execute the pipeline
result = pipeline_manager.execute(pipeline, input_data)
```

### 2. Event-Driven Architecture

The examples demonstrate how to use the event system for responsive applications:

```python
# Register event handlers
event_manager.register("device.connected", handle_device_connected)
event_manager.register("sensor.reading", handle_sensor_reading)
event_manager.register("automation.complete", handle_automation_complete)

# Emit events
event_manager.emit("device.connected", {"device_id": "dev1", "type": "gpio"})
```

### 3. Dynamic Configuration

The examples show how to use dynamic configuration for flexible applications:

```python
# Load configuration
config = ConfigManager.load("config/advanced.yaml")

# Access configuration with fallbacks
host = config.get("server.host", fallback="localhost")
port = config.get("server.port", fallback=8080)
```

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- Required dependencies (`pip install -r requirements.txt`)

For hardware-dependent examples, you can use simulation mode:

```bash
SIMULATION=1 python automation_example.py
```

## Configuration

Each example can be configured using YAML files in the `config/` directory:

- `automation.yaml`: Configuration for the automation example
- `devices.yaml`: Device definitions for hardware control
- `pipeline.yaml`: Pipeline definitions for data processing

## Additional Resources

- See the [UnitMCP Documentation](../../docs/README.md) for more information
- Check the [API Reference](../../docs/api/README.md) for detailed API documentation
- View the [Architecture Guide](../../docs/architecture/README.md) for system design information
