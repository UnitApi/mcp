# UnitMCP Hardware Guide

This guide provides information about hardware support in UnitMCP.

## Supported Hardware

UnitMCP supports a wide range of hardware devices, including:

### GPIO Devices
- LEDs
- Buttons
- Switches
- Relays
- Traffic lights

### Sensors
- Temperature sensors
- Humidity sensors
- Light sensors
- Motion sensors

### Displays
- LCD displays
- OLED displays
- E-paper displays

### Input Devices
- Keyboards
- Mice
- Joysticks

### Audio Devices
- Microphones
- Speakers

### Camera Devices
- USB cameras
- Raspberry Pi Camera Module

## Hardware Abstraction Layer

UnitMCP provides a hardware abstraction layer (HAL) that allows you to interact with hardware devices using a consistent API, regardless of the underlying hardware platform.

### Device Modes

UnitMCP supports multiple operational modes for hardware devices:

- **Hardware Mode**: Direct control of physical hardware
- **Simulation Mode**: Simulated hardware for development and testing
- **Remote Mode**: Control of hardware on a remote device
- **Mock Mode**: Mock implementations for testing

### Device Factory

The `DeviceFactory` class provides a factory pattern for creating device instances based on configuration:

```python
from unitmcp.hardware.factory import DeviceFactory

# Create a device factory
factory = DeviceFactory()

# Create a device from configuration
led = await factory.create_device({
    "type": "led",
    "pin": 17,
    "name": "Status LED"
})

# Control the device
await led.on()
```

### Mock Device Factory

For testing and development, UnitMCP provides a `MockDeviceFactory` that creates mock implementations of hardware devices:

```python
from unitmcp.dsl.converters.mock_factory import MockDeviceFactory

# Create a mock device factory
factory = MockDeviceFactory()

# Create a mock device
led = await factory.create_device({
    "type": "led",
    "pin": 17,
    "name": "Status LED"
})

# Control the mock device
await led.on()
```

## Platform-Specific Hardware Support

### Raspberry Pi

UnitMCP provides comprehensive support for Raspberry Pi hardware, including:

- GPIO pins
- I2C devices
- SPI devices
- UART devices
- Raspberry Pi Camera Module

### PC/Mac

On PC and Mac platforms, UnitMCP supports:

- USB devices
- Audio devices
- Camera devices
- Input devices

## Hardware Configuration

Hardware devices can be configured using YAML configuration files:

```yaml
devices:
  led1:
    type: led
    pin: 17
    name: Status LED
  button1:
    type: button
    pin: 18
    name: Control Button
  display1:
    type: display
    name: Info Display
```

See the [DSL Configuration Guide](../dsl/README.md) for more details on configuring hardware devices.
