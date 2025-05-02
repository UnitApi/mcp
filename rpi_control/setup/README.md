# Raspberry Pi Hardware Setup Scripts

This directory contains a collection of setup scripts for configuring and testing various hardware components on a Raspberry Pi. Each script handles the installation of necessary Linux packages, Python libraries, drivers, and system configurations specific to that hardware.

## Overview

The setup scripts are organized by hardware component, with each component having its own dedicated directory. The scripts will:

1. Install required system packages
2. Install necessary Python libraries
3. Configure the Raspberry Pi (enable interfaces, load kernel modules)
4. Set up proper permissions
5. Test the hardware functionality
6. Create example scripts for using the hardware

## Main Setup Script

The main entry point is `setup_all.py`, which allows you to set up individual components or all components at once.

```bash
# Set up a specific component
python3 setup_all.py --component lcd

# Set up all components
python3 setup_all.py --all

# Set up a component and reboot if necessary
python3 setup_all.py --component i2c --force-reboot
```

## Available Components

### LCD Display (`lcd`)
- Configures I2C interface
- Installs LCD libraries (RPLCD, smbus2)
- Detects connected LCD displays
- Tests LCD functionality
- Creates example scripts

### GPIO (`gpio`)
- Installs GPIO libraries (RPi.GPIO, gpiozero)
- Sets up proper permissions
- Tests GPIO functionality
- Creates example scripts for basic GPIO operations

### I2C Interface (`i2c`)
- Enables I2C in Raspberry Pi configuration
- Loads necessary kernel modules
- Sets up proper permissions
- Detects connected I2C devices
- Creates example scripts for I2C communication

### SPI Interface (`spi`)
- Enables SPI in Raspberry Pi configuration
- Loads necessary kernel modules
- Sets up proper permissions
- Tests SPI functionality
- Creates example scripts for SPI communication

### Audio (`audio`)
- Configures audio settings
- Tests audio input/output
- Creates example scripts for audio playback and recording

### LED Matrix (`led_matrix`)
- Sets up libraries for LED matrix displays
- Tests LED matrix functionality
- Creates example scripts for displaying patterns and text

### Camera (`camera`)
- Enables camera interface
- Installs necessary libraries
- Tests camera functionality
- Creates example scripts for capturing images and video

### Sensors (`sensors`)
- Configures various sensor types (temperature, humidity, motion, etc.)
- Tests sensor functionality
- Creates example scripts for reading sensor data

## Individual Component Setup

You can also run the setup scripts for individual components directly:

```bash
# Set up LCD display
python3 lcd/setup_lcd.py

# Set up GPIO
python3 gpio/setup_gpio.py

# Set up I2C interface
python3 i2c/setup_i2c.py

# Set up SPI interface
python3 spi/setup_spi.py
```

## Requirements

- Raspberry Pi running Raspberry Pi OS (Raspbian)
- Internet connection for package installation
- User with sudo privileges

## Troubleshooting

If you encounter issues with a specific hardware component:

1. Check the physical connections
2. Run the specific setup script with verbose logging
3. Verify that the required interfaces are enabled in `raspi-config`
4. Check that the user has the necessary permissions
5. Reboot the Raspberry Pi after making configuration changes

## Example Usage

After setting up a component, you can run the example scripts created in `/usr/local/bin/`:

```bash
# LCD example
lcd_example.py

# GPIO example
gpio_example.py

# I2C example
i2c_example.py

# SPI example
spi_example.py
```
