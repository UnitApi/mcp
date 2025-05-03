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

## Remote Setup

You can also set up hardware on a remote Raspberry Pi using the `remote_setup.py` script. This script will copy the setup files to the Raspberry Pi and execute them remotely.

```bash
# Set up LCD display on a remote Raspberry Pi
python3 remote_setup.py --host 192.168.1.2 --user pi --component lcd

# Set up all components on a remote Raspberry Pi
python3 remote_setup.py --host 192.168.1.2 --user pi --all

# Set up I2C interface and reboot if necessary
python3 remote_setup.py --host 192.168.1.2 --user pi --component i2c --force-reboot

# Run setup in simulation mode (no physical hardware or sudo required)
python3 remote_setup.py --host 192.168.1.2 --user pi --component oled --simulation
```

The remote setup script:
1. Checks the SSH connection to your Raspberry Pi
2. Creates a setup directory on the Pi
3. Copies all the necessary setup files to the Pi
4. Runs the appropriate setup script on the Pi
5. Displays real-time output of the setup process

### Simulation Mode

The setup scripts now support a `--simulation` mode that allows you to run the setup process without requiring physical hardware or sudo privileges. This is useful for:

- Testing the setup scripts in a development environment
- Verifying script functionality without modifying the system
- Running setup scripts on systems where sudo access is restricted
- Previewing what a setup script will do before running it with full privileges

When running in simulation mode:
- System package installation is skipped
- Python package installation is skipped
- Hardware interface enabling is simulated
- Hardware tests are simulated to succeed
- Example scripts are still created (in /tmp instead of /usr/local/bin)

To use simulation mode with the remote setup script:

```bash
python3 remote_setup.py --host raspberrypi.local --component oled --simulation
```

You can also use simulation mode directly with individual setup scripts:

```bash
python3 oled/setup_oled.py --simulation
```

Currently, simulation mode is supported for the following components:
- OLED displays
- (More components will be added in future updates)

## Available Components

### Basic Interfaces

#### I2C Interface (`i2c`)
- Enables I2C in Raspberry Pi configuration
- Loads necessary kernel modules
- Sets up proper permissions
- Detects connected I2C devices
- Creates example scripts for I2C communication

#### SPI Interface (`spi`)
- Enables SPI in Raspberry Pi configuration
- Loads necessary kernel modules
- Sets up proper permissions
- Tests SPI functionality
- Creates example scripts for SPI communication

#### GPIO (`gpio`)
- Installs GPIO libraries (RPi.GPIO, gpiozero)
- Sets up proper permissions
- Tests GPIO functionality
- Creates example scripts for basic GPIO operations

#### UART (`uart`)
- Enables UART/Serial interface
- Configures serial port settings
- Tests serial communication
- Creates example scripts for sending/receiving data

#### PWM (`pwm`)
- Configures PWM (Pulse Width Modulation) functionality
- Tests PWM output
- Creates example scripts for controlling LED brightness, motor speed, etc.

### Display Components

#### LCD Display (`lcd`)
- Configures I2C interface
- Installs LCD libraries (RPLCD, smbus2)
- Detects connected LCD displays
- Tests LCD functionality
- Creates example scripts

#### OLED Display (`oled`)
- Configures I2C/SPI interface for OLED displays
- Installs OLED libraries (Adafruit_SSD1306, luma.oled)
- Tests OLED display functionality
- Creates example scripts for displaying text and graphics

#### LED Matrix (`led_matrix`)
- Sets up libraries for LED matrix displays
- Tests LED matrix functionality
- Creates example scripts for displaying patterns and text

### Input/Output Devices

#### Servo Motors (`servo`)
- Configures GPIO for servo control
- Installs necessary libraries
- Tests servo movement
- Creates example scripts for controlling servo position

#### Stepper Motors (`stepper`)
- Configures GPIO for stepper motor control
- Installs stepper motor libraries
- Tests stepper motor movement
- Creates example scripts for precise motor control

#### Relay Modules (`relay`)
- Configures GPIO for relay control
- Tests relay switching
- Creates example scripts for controlling high-voltage devices

#### NeoPixel LEDs (`neopixel`)
- Configures GPIO for NeoPixel control
- Installs NeoPixel libraries (rpi_ws281x)
- Tests NeoPixel color and animation
- Creates example scripts for LED patterns and effects

### Sensors

#### Temperature Sensors (`temperature`)
- Configures interfaces for temperature sensors (DS18B20, DHT22, etc.)
- Installs necessary libraries
- Tests temperature reading
- Creates example scripts for monitoring temperature

#### Pressure Sensors (`pressure`)
- Configures I2C for pressure sensors (BMP280, etc.)
- Installs necessary libraries
- Tests pressure reading
- Creates example scripts for monitoring pressure

#### Humidity Sensors (`humidity`)
- Configures interfaces for humidity sensors (DHT22, etc.)
- Installs necessary libraries
- Tests humidity reading
- Creates example scripts for monitoring humidity

#### Motion Sensors (`motion`)
- Configures GPIO for motion sensors (PIR, etc.)
- Tests motion detection
- Creates example scripts for detecting movement

#### Distance Sensors (`distance`)
- Configures GPIO for distance sensors (HC-SR04, VL53L0X, etc.)
- Installs necessary libraries
- Tests distance measurement
- Creates example scripts for measuring distance

#### Accelerometer (`accelerometer`)
- Configures I2C for accelerometer sensors (MPU6050, ADXL345, etc.)
- Installs necessary libraries
- Tests acceleration measurement
- Creates example scripts for detecting movement and orientation

#### Gyroscope (`gyroscope`)
- Configures I2C for gyroscope sensors (MPU6050, etc.)
- Installs necessary libraries
- Tests rotation measurement
- Creates example scripts for detecting rotation

#### RFID/NFC (`rfid`)
- Configures SPI for RFID readers (MFRC522, PN532, etc.)
- Installs necessary libraries
- Tests RFID tag reading
- Creates example scripts for RFID authentication and data reading

### Other Peripherals

#### Camera (`camera`)
- Enables camera interface
- Installs necessary libraries
- Tests camera functionality
- Creates example scripts for capturing images and video

#### Audio (`audio`)
- Configures audio settings
- Tests audio input/output
- Creates example scripts for audio playback and recording

#### Analog-to-Digital Converter (`adc`)
- Configures interface for ADC chips (MCP3008, ADS1115, etc.)
- Installs necessary libraries
- Tests analog reading
- Creates example scripts for reading analog sensors

#### Digital-to-Analog Converter (`dac`)
- Configures interface for DAC chips (MCP4725, etc.)
- Installs necessary libraries
- Tests analog output
- Creates example scripts for generating analog signals

#### Real-Time Clock (`rtc`)
- Configures I2C for RTC modules (DS3231, PCF8523, etc.)
- Installs necessary libraries
- Tests time reading/setting
- Creates example scripts for maintaining accurate time

### Wireless Interfaces

#### Bluetooth (`bluetooth`)
- Configures Bluetooth interface
- Installs necessary libraries and tools
- Tests Bluetooth connectivity
- Creates example scripts for Bluetooth communication

#### WiFi (`wifi`)
- Configures WiFi interface
- Sets up network connections
- Tests WiFi connectivity
- Creates example scripts for network operations

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
- For remote setup: SSH access to the Raspberry Pi

## Troubleshooting

If you encounter issues with a specific hardware component:

1. Check the physical connections
2. Run the specific setup script with verbose logging
3. Verify that the required interfaces are enabled in `raspi-config`
4. Check that the user has the necessary permissions
5. Reboot the Raspberry Pi after making configuration changes

For remote setup issues:
1. Make sure your Raspberry Pi is powered on and connected to the network
2. Verify that SSH is enabled on your Raspberry Pi
3. Check that you're using the correct IP address and username

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
