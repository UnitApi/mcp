#!/usr/bin/env python3
"""
GPIO Setup Script for Raspberry Pi

This script installs all necessary dependencies and configures the system
for working with GPIO pins on the Raspberry Pi.

Usage:
  python3 setup_gpio.py [--force-reboot]

Options:
  --force-reboot  Reboot the Pi if configuration changes require it
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

# Define required packages
REQUIRED_PACKAGES = {
    "system": ["python3-dev", "python3-pip", "python3-rpi.gpio"],
    "python": ["RPi.GPIO", "gpiozero"]
}

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

def check_system_package(package: str) -> bool:
    """Check if a system package is installed."""
    logger.info(f"Checking if system package '{package}' is installed...")
    returncode, stdout, stderr = run_command(["dpkg", "-s", package], check=False)
    return returncode == 0

def install_system_package(package: str) -> bool:
    """Install a system package."""
    logger.info(f"Installing system package '{package}'...")
    returncode, stdout, stderr = run_command(["sudo", "apt-get", "install", "-y", package])
    if returncode == 0:
        logger.info(f"Successfully installed '{package}'")
        return True
    else:
        logger.error(f"Failed to install '{package}': {stderr}")
        return False

def check_python_package(package: str) -> bool:
    """Check if a Python package is installed."""
    logger.info(f"Checking if Python package '{package}' is installed...")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "pip", "show", package], check=False)
    return returncode == 0

def install_python_package(package: str) -> bool:
    """Install a Python package."""
    logger.info(f"Installing Python package '{package}'...")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "--user", package])
    if returncode == 0:
        logger.info(f"Successfully installed '{package}'")
        return True
    else:
        logger.error(f"Failed to install '{package}': {stderr}")
        return False

def fix_gpio_permissions() -> bool:
    """Fix GPIO permissions."""
    logger.info("Fixing GPIO permissions...")
    
    # Create/update udev rule for GPIO
    udev_rule = 'SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", PROGRAM="/bin/sh -c \'chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport ; chmod 220 /sys/class/gpio/export /sys/class/gpio/unexport\'"'
    udev_rule += '\nSUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", PROGRAM="/bin/sh -c \'chown root:gpio /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value ; chmod 660 /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value\'"'
    
    try:
        # Create gpio group if it doesn't exist
        returncode, stdout, stderr = run_command(
            ["getent", "group", "gpio"],
            check=False
        )
        
        if returncode != 0:
            logger.info("Creating gpio group...")
            run_command(["sudo", "groupadd", "-f", "gpio"])
        
        # Add current user to gpio group
        current_user = os.environ.get("USER", "pi")
        logger.info(f"Adding user {current_user} to gpio group...")
        run_command(["sudo", "usermod", "-aG", "gpio", current_user])
        
        # Create udev rule
        with open("/tmp/99-gpio-permissions.rules", "w") as f:
            f.write(udev_rule)
        
        run_command([
            "sudo", "cp", "/tmp/99-gpio-permissions.rules",
            "/etc/udev/rules.d/99-gpio-permissions.rules"
        ])
        
        # Reload udev rules
        run_command(["sudo", "udevadm", "control", "--reload-rules"])
        run_command(["sudo", "udevadm", "trigger"])
        
        logger.info("Fixed GPIO permissions")
        return True
    except Exception as e:
        logger.error(f"Failed to fix GPIO permissions: {e}")
        return False

def test_gpio() -> bool:
    """Test GPIO functionality."""
    logger.info("Testing GPIO functionality...")
    
    try:
        # Try to import RPi.GPIO
        import RPi.GPIO as GPIO
        
        # Set up GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Define test pins (adjust as needed)
        output_pin = 17  # GPIO17
        input_pin = 27   # GPIO27
        
        # Set up pins
        GPIO.setup(output_pin, GPIO.OUT)
        GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Test output pin
        logger.info(f"Testing output on GPIO{output_pin}...")
        GPIO.output(output_pin, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(output_pin, GPIO.LOW)
        
        # Test input pin
        logger.info(f"Testing input on GPIO{input_pin}...")
        input_value = GPIO.input(input_pin)
        logger.info(f"Input value on GPIO{input_pin}: {input_value}")
        
        # Clean up
        GPIO.cleanup()
        
        logger.info("GPIO test completed successfully")
        return True
    except ImportError:
        logger.error("RPi.GPIO library not available. Install with: pip install RPi.GPIO")
        return False
    except Exception as e:
        logger.error(f"Error testing GPIO: {e}")
        return False

def test_gpiozero() -> bool:
    """Test GPIO functionality using gpiozero."""
    logger.info("Testing GPIO functionality with gpiozero...")
    
    try:
        # Try to import gpiozero
        from gpiozero import LED, Button
        
        # Define test pins (adjust as needed)
        output_pin = 17  # GPIO17
        input_pin = 27   # GPIO27
        
        # Set up LED and Button
        led = LED(output_pin)
        button = Button(input_pin, pull_up=True)
        
        # Test LED
        logger.info(f"Testing LED on GPIO{output_pin}...")
        led.on()
        time.sleep(1)
        led.off()
        
        # Test Button
        logger.info(f"Testing Button on GPIO{input_pin}...")
        logger.info(f"Button is {'pressed' if button.is_pressed else 'not pressed'}")
        
        logger.info("gpiozero test completed successfully")
        return True
    except ImportError:
        logger.error("gpiozero library not available. Install with: pip install gpiozero")
        return False
    except Exception as e:
        logger.error(f"Error testing gpiozero: {e}")
        return False

def install_dependencies() -> bool:
    """Install all required dependencies."""
    logger.info("Installing dependencies...")
    
    # Update package lists
    logger.info("Updating package lists...")
    run_command(["sudo", "apt-get", "update"])
    
    # Install system packages
    all_system_installed = True
    for package in REQUIRED_PACKAGES["system"]:
        if not check_system_package(package):
            if not install_system_package(package):
                all_system_installed = False
    
    # Install Python packages
    all_python_installed = True
    for package in REQUIRED_PACKAGES["python"]:
        if not check_python_package(package):
            if not install_python_package(package):
                all_python_installed = False
    
    return all_system_installed and all_python_installed

def create_example_script() -> bool:
    """Create an example script for using GPIO."""
    logger.info("Creating example script...")
    
    example_script = """#!/usr/bin/env python3
'''
GPIO Example Script

This script demonstrates how to use GPIO pins on the Raspberry Pi.
'''

import time
import sys
import RPi.GPIO as GPIO

def main():
    try:
        # Set up GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Define pins
        led_pin = 17  # GPIO17
        button_pin = 27  # GPIO27
        
        # Set up pins
        GPIO.setup(led_pin, GPIO.OUT)
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print("GPIO Example Script")
        print("Press the button to toggle the LED")
        print("Press Ctrl+C to exit")
        
        # Initial state
        led_state = False
        GPIO.output(led_pin, led_state)
        
        # Main loop
        while True:
            # Check if button is pressed (active low)
            if GPIO.input(button_pin) == GPIO.LOW:
                # Toggle LED
                led_state = not led_state
                GPIO.output(led_pin, led_state)
                print(f"LED {'ON' if led_state else 'OFF'}")
                
                # Debounce
                time.sleep(0.2)
            
            # Small delay to reduce CPU usage
            time.sleep(0.1)
        
        return 0
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        GPIO.cleanup()

if __name__ == "__main__":
    sys.exit(main())
"""
    
    try:
        # Create the example script
        with open("/tmp/gpio_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        run_command(["sudo", "cp", "/tmp/gpio_example.py", "/usr/local/bin/gpio_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/gpio_example.py"])
        
        logger.info("Created example script at /usr/local/bin/gpio_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def create_gpiozero_example_script() -> bool:
    """Create an example script for using gpiozero."""
    logger.info("Creating gpiozero example script...")
    
    example_script = """#!/usr/bin/env python3
'''
GPIO Zero Example Script

This script demonstrates how to use the gpiozero library on the Raspberry Pi.
'''

import time
import sys
from gpiozero import LED, Button
from signal import pause

def main():
    try:
        # Define components
        led = LED(17)  # GPIO17
        button = Button(27, pull_up=True)  # GPIO27
        
        print("GPIO Zero Example Script")
        print("Press the button to toggle the LED")
        print("Press Ctrl+C to exit")
        
        # Set up button to toggle LED
        button.when_pressed = led.toggle
        
        # Wait for events
        pause()
        
        return 0
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    try:
        # Create the example script
        with open("/tmp/gpiozero_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        run_command(["sudo", "cp", "/tmp/gpiozero_example.py", "/usr/local/bin/gpiozero_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/gpiozero_example.py"])
        
        logger.info("Created gpiozero example script at /usr/local/bin/gpiozero_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create gpiozero example script: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="GPIO Setup Script for Raspberry Pi")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    logger.info("Starting GPIO setup...")
    
    # Install dependencies
    if not install_dependencies():
        logger.warning("Some dependencies could not be installed")
    
    # Fix GPIO permissions
    fix_gpio_permissions()
    
    # Test GPIO functionality
    gpio_works = test_gpio()
    gpiozero_works = test_gpiozero()
    
    # Create example scripts
    create_example_script()
    create_gpiozero_example_script()
    
    # Print summary
    logger.info("\n=== GPIO Setup Summary ===")
    logger.info(f"RPi.GPIO Working: {'Yes' if gpio_works else 'No'}")
    logger.info(f"gpiozero Working: {'Yes' if gpiozero_works else 'No'}")
    
    if gpio_works or gpiozero_works:
        logger.info("GPIO is working correctly!")
        logger.info("You can run the example scripts with:")
        logger.info("  gpio_example.py")
        logger.info("  gpiozero_example.py")
    else:
        logger.warning("GPIO could not be initialized.")
        logger.info("Please check the following:")
        logger.info("1. Make sure you are running on a Raspberry Pi")
        logger.info("2. Try running this script with sudo")
        logger.info("3. Try rebooting the Raspberry Pi")
    
    # Reboot if required and --force-reboot is specified
    if args.force_reboot:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0 if (gpio_works or gpiozero_works) else 1

if __name__ == "__main__":
    sys.exit(main())
