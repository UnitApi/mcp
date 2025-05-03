# UnitMCP Platform-Specific Examples

This directory contains examples demonstrating UnitMCP integration with specific hardware platforms. Each subdirectory contains examples tailored to a particular hardware platform.

## Available Platforms

### Raspberry Pi

The [raspberry_pi](./raspberry_pi/) directory contains examples specifically designed for the Raspberry Pi platform:

```bash
# Navigate to the Raspberry Pi examples
cd raspberry_pi

# Run the GPIO example
python gpio_example.py
```

These examples demonstrate:
- GPIO pin control (digital input/output)
- PWM control for LEDs and motors
- I2C and SPI communication with sensors
- Hardware-specific optimizations for Raspberry Pi

## Platform Integration Features

UnitMCP provides platform-specific integrations that leverage the unique capabilities of each hardware platform:

### 1. Platform Detection

UnitMCP can automatically detect the platform it's running on:

```python
from unitmcp.platforms import platform_detector

# Detect the current platform
current_platform = platform_detector.detect_platform()
print(f"Running on: {current_platform}")

# Check if running on a specific platform
if platform_detector.is_raspberry_pi():
    # Use Raspberry Pi specific features
    from unitmcp.platforms.raspberry_pi import GPIO
```

### 2. Platform-Specific Optimizations

Each platform integration includes optimizations for that specific hardware:

```python
# Example of platform-specific optimization
from unitmcp.platforms import get_platform_manager

# Get the platform-specific manager
platform_manager = get_platform_manager()

# Use platform-optimized GPIO access
pin = platform_manager.setup_pin(17, "OUT")
platform_manager.write_pin(pin, True)
```

### 3. Consistent Cross-Platform API

UnitMCP provides a consistent API across different platforms:

```python
# Example of cross-platform code
from unitmcp.hardware import DeviceManager

# Create a device manager (works on any platform)
device_manager = DeviceManager()

# Add a device (platform-specific implementation is handled internally)
device_manager.add_device("led1", {
    "type": "led",
    "pin": 17,
    "active_high": True
})

# Control the device (works the same on any platform)
device_manager.control_device("led1", "on")
```

## Adding New Platform Support

To add support for a new platform:

1. Create a new directory under `platforms/` for your platform
2. Implement the platform-specific interfaces required by UnitMCP
3. Create examples demonstrating the platform-specific features
4. Update this README.md to include your new platform

## Running the Examples

To run these examples, you'll need:

- Python 3.7+
- UnitMCP library installed (`pip install -e .` from the project root)
- The specific hardware platform for the examples you want to run
- Platform-specific dependencies (listed in each platform's README)

## Platform-Specific Configuration

Each platform may have specific configuration options:

| Platform | Configuration File | Description |
|----------|-------------------|-------------|
| Raspberry Pi | `config/rpi.yaml` | Raspberry Pi specific settings |

## Additional Resources

- [UnitMCP Platform API Documentation](../../docs/api/platforms.md)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Platform Development Guide](../../docs/development/platforms.md)
