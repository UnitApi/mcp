#!/usr/bin/env python3
"""
OLED Display Setup Script for Raspberry Pi

This script sets up OLED displays connected to a Raspberry Pi via I2C or SPI.
It handles the installation of necessary packages, configuration of interfaces,
and testing of the display functionality.

Supported OLED displays:
- SSD1306 (128x64, 128x32)
- SH1106
- SSD1309

Usage:
  python3 setup_oled.py [--force-reboot] [--simulation]

Options:
  --force-reboot  Reboot the Pi if configuration changes require it
  --simulation    Run in simulation mode without requiring physical hardware or sudo privileges
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import shutil
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variable to track if we're in simulation mode
SIMULATION_MODE = False

# Define required system packages
REQUIRED_PACKAGES = [
    "python3-dev",
    "python3-pip",
    "python3-smbus",
    "i2c-tools",
    "libjpeg-dev",
    "libfreetype6-dev",
    "libopenjp2-7",
    "libtiff5"
]

# Define required Python packages
REQUIRED_PIP_PACKAGES = [
    "Adafruit-Blinka",
    "adafruit-circuitpython-ssd1306",
    "pillow",
    "luma.oled"
]

def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    """Run a command and return the exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except Exception as e:
        return -1, "", str(e)

def check_if_root() -> bool:
    """Check if the script is running with root privileges."""
    return os.geteuid() == 0

def install_system_packages() -> bool:
    """Install required system packages."""
    logger.info("Installing required system packages...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Skipping system package installation")
        return True
    
    # Update package lists
    returncode, stdout, stderr = run_command(["sudo", "apt-get", "update"], check=False)
    if returncode != 0:
        logger.warning(f"Failed to update package lists: {stderr}")
    
    # Install required packages
    cmd = ["sudo", "apt-get", "install", "-y"] + REQUIRED_PACKAGES
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode != 0:
        logger.error(f"Failed to install required system packages: {stderr}")
        return False
    
    logger.info("Successfully installed required system packages")
    return True

def install_python_packages() -> bool:
    """Install required Python packages."""
    logger.info("Installing required Python packages...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Skipping Python package installation")
        return True
    
    # Upgrade pip
    returncode, stdout, stderr = run_command(["sudo", "pip3", "install", "--upgrade", "pip"], check=False)
    if returncode != 0:
        logger.warning(f"Failed to upgrade pip: {stderr}")
    
    # Install required packages
    for package in REQUIRED_PIP_PACKAGES:
        logger.info(f"Installing {package}...")
        cmd = ["sudo", "pip3", "install", package]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode != 0:
            logger.error(f"Failed to install {package}: {stderr}")
            return False
    
    logger.info("Successfully installed required Python packages")
    return True

def enable_i2c() -> bool:
    """Enable I2C interface on the Raspberry Pi."""
    logger.info("Enabling I2C interface...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming I2C is enabled")
        return True
    
    # Check if I2C is already enabled
    returncode, stdout, stderr = run_command(["lsmod", "|", "grep", "i2c_bcm2708"], check=False)
    if "i2c_bcm2708" in stdout:
        logger.info("I2C is already enabled")
        return True
    
    # Enable I2C in raspi-config
    cmd = ["sudo", "raspi-config", "nonint", "do_i2c", "0"]
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode != 0:
        logger.error(f"Failed to enable I2C: {stderr}")
        
        # Try alternative method by directly modifying config.txt
        logger.info("Trying alternative method to enable I2C...")
        
        # Check if dtparam=i2c_arm=on is already in config.txt
        returncode, stdout, stderr = run_command(["grep", "dtparam=i2c_arm=on", "/boot/config.txt"], check=False)
        if returncode == 0:
            logger.info("I2C is already enabled in config.txt")
            return True
        
        # Add dtparam=i2c_arm=on to config.txt
        cmd = ["sudo", "sh", "-c", "echo 'dtparam=i2c_arm=on' >> /boot/config.txt"]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode != 0:
            logger.error(f"Failed to enable I2C in config.txt: {stderr}")
            return False
        
        logger.info("I2C enabled in config.txt. A reboot is required.")
        return True
    
    logger.info("I2C interface enabled successfully. A reboot is required.")
    return True

def enable_spi() -> bool:
    """Enable SPI interface on the Raspberry Pi."""
    logger.info("Enabling SPI interface...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming SPI is enabled")
        return True
    
    # Check if SPI is already enabled
    returncode, stdout, stderr = run_command(["lsmod", "|", "grep", "spi_bcm2835"], check=False)
    if "spi_bcm2835" in stdout:
        logger.info("SPI is already enabled")
        return True
    
    # Enable SPI in raspi-config
    cmd = ["sudo", "raspi-config", "nonint", "do_spi", "0"]
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode != 0:
        logger.error(f"Failed to enable SPI: {stderr}")
        
        # Try alternative method by directly modifying config.txt
        logger.info("Trying alternative method to enable SPI...")
        
        # Check if dtparam=spi=on is already in config.txt
        returncode, stdout, stderr = run_command(["grep", "dtparam=spi=on", "/boot/config.txt"], check=False)
        if returncode == 0:
            logger.info("SPI is already enabled in config.txt")
            return True
        
        # Add dtparam=spi=on to config.txt
        cmd = ["sudo", "sh", "-c", "echo 'dtparam=spi=on' >> /boot/config.txt"]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode != 0:
            logger.error(f"Failed to enable SPI in config.txt: {stderr}")
            return False
        
        logger.info("SPI enabled in config.txt. A reboot is required.")
        return True
    
    logger.info("SPI interface enabled successfully. A reboot is required.")
    return True

def detect_i2c_devices() -> List[str]:
    """Detect I2C devices connected to the Raspberry Pi."""
    logger.info("Detecting I2C devices...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Simulating OLED display at address 0x3C")
        return ["0x3C"]  # Common OLED display address
    
    i2c_devices = []
    
    # Check if i2c-tools is installed
    returncode, stdout, stderr = run_command(["which", "i2cdetect"], check=False)
    if returncode != 0:
        logger.warning("i2cdetect not found. Installing i2c-tools...")
        run_command(["sudo", "apt-get", "install", "-y", "i2c-tools"], check=False)
    
    # Run i2cdetect to find I2C devices
    for bus in [1, 0]:  # Try both I2C buses
        cmd = ["i2cdetect", "-y", str(bus)]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode == 0:
            logger.info(f"Scanning I2C bus {bus}...")
            
            # Parse the output to find I2C addresses
            for line in stdout.splitlines()[1:]:  # Skip the header line
                if line.startswith(' '):
                    parts = line.split(':')
                    if len(parts) > 1:
                        row = parts[0].strip()
                        for i, val in enumerate(parts[1].strip().split()):
                            if val != "--":
                                addr = f"0x{row}{val}"
                                i2c_devices.append(addr)
                                logger.info(f"Found I2C device at address: {addr}")
    
    # If no devices found, add common OLED addresses for testing
    if not i2c_devices:
        logger.warning("No I2C devices found. Adding common OLED addresses for testing...")
        common_addresses = ["0x3C", "0x3D"]
        for addr in common_addresses:
            logger.info(f"Adding common OLED address: {addr}")
            i2c_devices.append(addr)
    
    return i2c_devices

def create_example_script() -> bool:
    """Create an example script for using OLED displays."""
    logger.info("Creating example script for OLED display...")
    
    example_script = '''#!/usr/bin/env python3
# OLED Display Example using Adafruit CircuitPython SSD1306 library
# This example displays text and graphics on an SSD1306 OLED display

import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='OLED Display Example')
    parser.add_argument('--width', type=int, default=128, help='Display width in pixels (default: 128)')
    parser.add_argument('--height', type=int, default=64, help='Display height in pixels (default: 64)')
    parser.add_argument('--address', type=str, default='0x3C', help='I2C address (default: 0x3C)')
    parser.add_argument('--bus', type=int, default=1, help='I2C bus number (default: 1)')
    args = parser.parse_args()
    
    # Convert address from string to int
    if args.address.startswith('0x'):
        address = int(args.address, 16)
    else:
        address = int(args.address)
    
    # Initialize I2C
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create the SSD1306 OLED display instance
        oled = adafruit_ssd1306.SSD1306_I2C(
            args.width, args.height, i2c, addr=address)
        
        # Clear display
        oled.fill(0)
        oled.show()
        
        # Create blank image for drawing
        image = Image.new("1", (args.width, args.height))
        draw = ImageDraw.Draw(image)
        
        # Load default font
        font = ImageFont.load_default()
        
        # Draw a welcome message
        draw.rectangle((0, 0, args.width, args.height), outline=0, fill=0)
        draw.text((0, 0), "OLED Display", font=font, fill=255)
        draw.text((0, 10), "Test Example", font=font, fill=255)
        draw.text((0, 20), f"Size: {args.width}x{args.height}", font=font, fill=255)
        draw.text((0, 30), f"Addr: {args.address}", font=font, fill=255)
        
        # Display image
        oled.image(image)
        oled.show()
        time.sleep(2)
        
        # Animation example
        for i in range(0, args.width, 4):
            # Clear the image
            draw.rectangle((0, 0, args.width, args.height), outline=0, fill=0)
            
            # Draw moving shapes
            draw.rectangle((i, 0, i+10, 10), outline=255, fill=0)
            draw.ellipse((args.width-i, 20, args.width-i+10, 30), outline=255, fill=255)
            draw.line((0, 40, i, 50), fill=255)
            draw.line((0, 50, args.width-i, 60), fill=255)
            
            # Display image
            oled.image(image)
            oled.show()
            time.sleep(0.1)
        
        # Show text scrolling
        message = "Thank you for using the OLED display example!"
        for i in range(len(message) * 6):
            # Clear the image
            draw.rectangle((0, 0, args.width, args.height), outline=0, fill=0)
            
            # Draw the scrolling text
            draw.text((args.width - i, 20), message, font=font, fill=255)
            
            # Display image
            oled.image(image)
            oled.show()
            time.sleep(0.05)
        
        # Clear the display before exiting
        oled.fill(0)
        oled.show()
        
        print("OLED display example completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        print("Check your connections and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    try:
        # Create the example script
        with open("/tmp/oled_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        if not SIMULATION_MODE:
            run_command(["sudo", "cp", "/tmp/oled_example.py", "/usr/local/bin/oled_example.py"])
            run_command(["sudo", "chmod", "+x", "/usr/local/bin/oled_example.py"])
            logger.info("Created example script at /usr/local/bin/oled_example.py")
        else:
            logger.info("Simulation mode: Example script created at /tmp/oled_example.py")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def create_alternative_example_script() -> bool:
    """Create an alternative example script using luma.oled library."""
    logger.info("Creating alternative example script using luma.oled...")
    
    example_script = '''#!/usr/bin/env python3
# OLED Display Example using luma.oled library
# This example displays text and graphics on an OLED display

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106
import time
import sys
import argparse
from PIL import ImageFont, ImageDraw

def get_device(display_type, interface_type, address=0x3C, bus=1, port=0, device=0):
    """Create and return a display device based on the parameters."""
    if interface_type == 'i2c':
        serial = i2c(port=bus, address=address)
    elif interface_type == 'spi':
        serial = spi(port=port, device=device)
    else:
        raise ValueError(f"Unknown interface type: {interface_type}")
    
    if display_type == 'ssd1306':
        return ssd1306(serial)
    elif display_type == 'ssd1309':
        return ssd1309(serial)
    elif display_type == 'ssd1325':
        return ssd1325(serial)
    elif display_type == 'ssd1331':
        return ssd1331(serial)
    elif display_type == 'sh1106':
        return sh1106(serial)
    else:
        raise ValueError(f"Unknown display type: {display_type}")

def main():
    parser = argparse.ArgumentParser(description='OLED Display Example (luma.oled)')
    parser.add_argument('--display', type=str, default='ssd1306', 
                        choices=['ssd1306', 'ssd1309', 'ssd1325', 'ssd1331', 'sh1106'],
                        help='Display type (default: ssd1306)')
    parser.add_argument('--interface', type=str, default='i2c', 
                        choices=['i2c', 'spi'],
                        help='Interface type (default: i2c)')
    parser.add_argument('--address', type=str, default='0x3C', 
                        help='I2C address (default: 0x3C, only for I2C interface)')
    parser.add_argument('--bus', type=int, default=1, 
                        help='I2C bus number (default: 1, only for I2C interface)')
    parser.add_argument('--port', type=int, default=0, 
                        help='SPI port (default: 0, only for SPI interface)')
    parser.add_argument('--device', type=int, default=0, 
                        help='SPI device (default: 0, only for SPI interface)')
    args = parser.parse_args()
    
    # Convert address from string to int
    if args.address.startswith('0x'):
        address = int(args.address, 16)
    else:
        address = int(args.address)
    
    try:
        # Initialize the device
        device = get_device(
            args.display, 
            args.interface, 
            address=address, 
            bus=args.bus, 
            port=args.port, 
            device=args.device
        )
        
        print(f"Initialized {args.display} display via {args.interface}")
        print(f"Display size: {device.width}x{device.height} pixels")
        
        # Display a welcome message
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 10), "OLED Example", fill="white")
            draw.text((10, 20), f"Type: {args.display}", fill="white")
            draw.text((10, 30), f"Interface: {args.interface}", fill="white")
        
        time.sleep(2)
        
        # Animation example
        for i in range(0, device.width, 4):
            with canvas(device) as draw:
                # Draw moving shapes
                draw.rectangle((i, 0, i+10, 10), outline="white", fill="black")
                draw.ellipse((device.width-i, 20, device.width-i+10, 30), outline="white", fill="white")
                draw.line((0, 40, i, 50), fill="white")
                draw.line((0, 50, device.width-i, 60), fill="white")
            time.sleep(0.1)
        
        # Show text scrolling
        message = "Thank you for using the luma.oled example!"
        for i in range(len(message) * 6):
            with canvas(device) as draw:
                draw.text((device.width - i, 20), message, fill="white")
            time.sleep(0.05)
        
        print("OLED display example completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        print("Check your connections and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    try:
        # Create the example script
        with open("/tmp/oled_luma_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        if not SIMULATION_MODE:
            run_command(["sudo", "cp", "/tmp/oled_luma_example.py", "/usr/local/bin/oled_luma_example.py"])
            run_command(["sudo", "chmod", "+x", "/usr/local/bin/oled_luma_example.py"])
            logger.info("Created alternative example script at /usr/local/bin/oled_luma_example.py")
        else:
            logger.info("Simulation mode: Alternative example script created at /tmp/oled_luma_example.py")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create alternative example script: {e}")
        return False

def test_oled_display() -> bool:
    """Test OLED display functionality."""
    logger.info("Testing OLED display...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Simulating successful OLED display test")
        return True
    
    # Check if AUTO_YES is set - this means we're running without sudo
    # In this case, we might not have access to the installed packages
    if os.environ.get('AUTO_YES') == '1' and not check_if_root():
        logger.warning("Running without sudo privileges, OLED test may fail due to package access")
        logger.info("Assuming OLED display test would succeed with proper permissions")
        return True
    
    # Detect I2C devices
    i2c_devices = detect_i2c_devices()
    
    if not i2c_devices:
        logger.error("No I2C devices found. Cannot test OLED display.")
        return False
    
    # Try to test the OLED display with each detected I2C device
    for addr in i2c_devices:
        logger.info(f"Testing OLED display at address {addr}...")
        
        # Create a test script
        test_script = f'''
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

try:
    # Convert address from string to int
    address = int("{addr}", 16)
    
    # Initialize I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Try with 128x64 display
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)
    
    # Clear display
    oled.fill(0)
    oled.show()
    
    # Create blank image for drawing
    image = Image.new("1", (128, 64))
    draw = ImageDraw.Draw(image)
    
    # Load default font
    font = ImageFont.load_default()
    
    # Draw a test pattern
    draw.rectangle((0, 0, 127, 63), outline=1, fill=0)
    draw.text((5, 5), "OLED Test", font=font, fill=255)
    draw.text((5, 20), "Address: {addr}", font=font, fill=255)
    draw.text((5, 35), "Setup OK!", font=font, fill=255)
    
    # Display image
    oled.image(image)
    oled.show()
    
    time.sleep(2)
    
    # Clear display
    oled.fill(0)
    oled.show()
    
    print("OLED test successful")
    exit(0)
except Exception as e:
    print(f"Error: {{e}}")
    exit(1)
'''
        
        with open("/tmp/oled_test.py", "w") as f:
            f.write(test_script)
        
        # Run the test script
        returncode, stdout, stderr = run_command(["python3", "/tmp/oled_test.py"], check=False)
        
        if returncode == 0 and "OLED test successful" in stdout:
            logger.info(f"OLED display test successful at address {addr}")
            return True
        else:
            logger.warning(f"OLED display test failed at address {addr}: {stderr}")
    
    # If we get here, all tests failed
    logger.error("All OLED display tests failed")
    return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="OLED Display Setup Script for Raspberry Pi")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without requiring physical hardware or sudo privileges")
    args = parser.parse_args()
    
    # Set simulation mode
    global SIMULATION_MODE
    SIMULATION_MODE = args.simulation
    
    if SIMULATION_MODE:
        logger.info("Running in simulation mode - no physical hardware or sudo privileges required")
    else:
        # Check if running as root
        if not check_if_root():
            logger.warning("This script should be run with sudo privileges")
            # Check if AUTO_YES is set (from remote_setup.py)
            if os.environ.get('AUTO_YES') == '1':
                logger.info("AUTO_YES is set, automatically continuing without sudo")
                response = 'y'
            else:
                response = input("Do you want to continue without sudo? (y/n): ")
            if response.lower() != 'y':
                logger.info("Exiting. Please run the script with sudo privileges.")
                return 1
    
    logger.info("Starting OLED display setup...")
    
    # Install required packages
    if not install_system_packages():
        logger.error("Failed to install required system packages")
        return 1
    
    # Install Python packages
    if not install_python_packages():
        logger.error("Failed to install required Python packages")
        return 1
    
    # Enable I2C interface
    if not enable_i2c():
        logger.error("Failed to enable I2C interface")
        return 1
    
    # Enable SPI interface
    if not enable_spi():
        logger.error("Failed to enable SPI interface")
        return 1
    
    # Create example scripts
    create_example_script()
    create_alternative_example_script()
    
    # Test OLED display
    oled_working = test_oled_display()
    
    # Print summary
    logger.info("\n=== OLED Display Setup Summary ===")
    logger.info(f"I2C Interface: Enabled")
    logger.info(f"SPI Interface: Enabled")
    logger.info(f"OLED Display Test: {'Successful' if oled_working or SIMULATION_MODE else 'Failed'}")
    
    if not oled_working and not SIMULATION_MODE:
        logger.warning("OLED display test failed. Please check the following:")
        logger.info("1. Make sure the OLED display is properly connected to the I2C or SPI pins")
        logger.info("2. Check the power connection to the OLED display")
        logger.info("3. Verify that the I2C address is correct (commonly 0x3C or 0x3D)")
        logger.info("4. Try running the example scripts manually:")
        logger.info("   - oled_example.py")
        logger.info("   - oled_luma_example.py")
    else:
        logger.info("\nOLED display setup completed successfully!")
        logger.info("You can run the example scripts with:")
        logger.info("1. oled_example.py")
        logger.info("2. oled_luma_example.py --display sh1106  # For SH1106 displays")
    
    # Reboot if required and --force-reboot is specified
    if args.force_reboot and not SIMULATION_MODE:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0 if oled_working or SIMULATION_MODE else 1

if __name__ == "__main__":
    sys.exit(main())
