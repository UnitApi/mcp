#!/usr/bin/env python3
"""
NeoPixel LED Setup and Test Script

This script focuses on setting up and testing NeoPixel LED strips/rings
connected to a Raspberry Pi. It will:

1. Install necessary dependencies for controlling NeoPixel LEDs
2. Configure the system for proper NeoPixel operation
3. Test the NeoPixel LEDs with various patterns
4. Create example scripts for future use

Usage:
  python3 setup_neopixel.py [--pin PIN] [--count COUNT] [--simulation]

Options:
  --pin PIN          GPIO pin number connected to the NeoPixel data line (default: 18)
  --count COUNT      Number of NeoPixel LEDs in the strip/ring (default: 16)
  --simulation       Run in simulation mode without requiring physical hardware
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

def setup_neopixel_libraries() -> bool:
    """Install and set up NeoPixel libraries."""
    logger.info("Installing NeoPixel dependencies...")
    
    # Update package lists
    logger.info("Updating package lists...")
    run_command(["sudo", "apt-get", "update"], check=False)
    
    # Install system packages
    system_packages = ["python3-pip", "python3-dev", "build-essential", "swig", "scons", "git"]
    for package in system_packages:
        logger.info(f"Checking if system package '{package}' is installed...")
        returncode, stdout, stderr = run_command(["dpkg", "-s", package], check=False)
        if returncode != 0:
            logger.info(f"Installing system package '{package}'...")
            run_command(["sudo", "apt-get", "install", "-y", package], check=False)
    
    # Install Python packages
    python_packages = ["rpi_ws281x", "adafruit-circuitpython-neopixel"]
    for package in python_packages:
        logger.info(f"Checking if Python package '{package}' is installed...")
        returncode, stdout, stderr = run_command(
            [sys.executable, "-m", "pip", "show", package],
            check=False
        )
        if returncode != 0:
            logger.info(f"Installing Python package '{package}'...")
            returncode, stdout, stderr = run_command(
                ["sudo", sys.executable, "-m", "pip", "install", package],
                check=False
            )
            if returncode == 0:
                logger.info(f"Successfully installed '{package}'")
            else:
                logger.error(f"Failed to install '{package}': {stderr}")
    
    # Install Blinka if needed (for CircuitPython)
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "show", "Adafruit-Blinka"],
        check=False
    )
    if returncode != 0:
        logger.info("Installing Adafruit-Blinka...")
        run_command(["sudo", sys.executable, "-m", "pip", "install", "Adafruit-Blinka"], check=False)
    
    return True

def configure_system_for_neopixel() -> bool:
    """Configure the system for NeoPixel operation."""
    logger.info("Configuring system for NeoPixel operation...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Skipping system configuration")
        return True
    
    # Check if audio is disabled in config.txt (required for PWM on GPIO18)
    audio_disabled = False
    config_modified = False
    
    try:
        with open("/boot/config.txt", "r") as f:
            config = f.read()
            if "dtparam=audio=off" in config or "dtparam=audio=0" in config:
                audio_disabled = True
                logger.info("Audio is already disabled in /boot/config.txt")
    except Exception as e:
        logger.error(f"Could not check config.txt: {e}")
    
    # Disable audio if needed (required for PWM on GPIO18)
    if not audio_disabled:
        logger.warning("Audio must be disabled for NeoPixels on GPIO18")
        try:
            # Backup config.txt
            run_command(["sudo", "cp", "/boot/config.txt", "/boot/config.txt.bak"])
            
            # Add audio configuration
            run_command([
                "sudo", "bash", "-c",
                "echo '\n# Disable audio for NeoPixel support\ndtparam=audio=off' >> /boot/config.txt"
            ])
            
            logger.info("Disabled audio in /boot/config.txt")
            config_modified = True
        except Exception as e:
            logger.error(f"Failed to modify config.txt: {e}")
    
    # Add user to gpio group
    current_user = os.environ.get("USER", "pi")
    logger.info(f"Adding user {current_user} to gpio group...")
    run_command(["sudo", "usermod", "-aG", "gpio", current_user], check=False)
    
    return True

def test_neopixel(pin: int = 18, count: int = 16) -> bool:
    """Test the NeoPixel LEDs with various patterns."""
    logger.info(f"Testing NeoPixel LEDs on pin {pin} with {count} LEDs...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Simulating successful NeoPixel test")
        return True
    
    # Create a test script
    test_script = f"""
import time
import board
import neopixel

# Choose an open pin connected to the Data In of the NeoPixel strip
# Using D18 (GPIO18) as the default
pixel_pin = board.D{pin}

# The number of NeoPixel LEDs
num_pixels = {count}

# Initialize the NeoPixels
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB
)

def color_wipe(color, wait):
    for i in range(num_pixels):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            rc_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)

try:
    # Clear all pixels
    pixels.fill((0, 0, 0))
    pixels.show()
    
    print("Running color wipe (red)")
    color_wipe((255, 0, 0), 0.05)  # Red wipe
    time.sleep(0.5)
    
    print("Running color wipe (green)")
    color_wipe((0, 255, 0), 0.05)  # Green wipe
    time.sleep(0.5)
    
    print("Running color wipe (blue)")
    color_wipe((0, 0, 255), 0.05)  # Blue wipe
    time.sleep(0.5)
    
    print("Running rainbow cycle")
    rainbow_cycle(0.001)  # Rainbow cycle
    
    # Clear all pixels
    pixels.fill((0, 0, 0))
    pixels.show()
    
    print("NeoPixel test successful")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
"""
    
    with open("/tmp/neopixel_test.py", "w") as f:
        f.write(test_script)
    
    # Run the test script
    logger.info("Running NeoPixel test...")
    returncode, stdout, stderr = run_command(["sudo", sys.executable, "/tmp/neopixel_test.py"], check=False)
    
    if returncode == 0 and "NeoPixel test successful" in stdout:
        logger.info("NeoPixel test successful")
        return True
    else:
        logger.error(f"NeoPixel test failed: {stderr}")
        return False

def create_example_script(pin: int = 18, count: int = 16) -> bool:
    """Create an example script for using NeoPixel LEDs."""
    logger.info("Creating example script...")
    
    example_script = f"""#!/usr/bin/env python3
# NeoPixel Example Script
# This script demonstrates how to use NeoPixel LEDs with a Raspberry Pi

import time
import board
import neopixel
import argparse
import sys

# Default configuration
DEFAULT_PIN = {pin}
DEFAULT_COUNT = {count}
DEFAULT_BRIGHTNESS = 0.2

def color_wipe(pixels, color, wait):
    """Color wipe animation."""
    for i in range(len(pixels)):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

def theater_chase(pixels, color, wait):
    """Theater chase animation."""
    for j in range(10):
        for q in range(3):
            for i in range(0, len(pixels), 3):
                if i + q < len(pixels):
                    pixels[i + q] = color
            pixels.show()
            time.sleep(wait)
            for i in range(0, len(pixels), 3):
                if i + q < len(pixels):
                    pixels[i + q] = (0, 0, 0)

def rainbow(pixels, wait):
    """Rainbow animation."""
    for j in range(255):
        for i in range(len(pixels)):
            pixels[i] = wheel(i + j)
        pixels.show()
        time.sleep(wait)

def rainbow_cycle(pixels, wait):
    """Rainbow cycle animation."""
    for j in range(255):
        for i in range(len(pixels)):
            rc_index = (i * 256 // len(pixels)) + j
            pixels[i] = wheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)

def main():
    parser = argparse.ArgumentParser(description="NeoPixel LED Example")
    parser.add_argument("--pin", type=int, default=DEFAULT_PIN, help=f"GPIO pin number (default: {DEFAULT_PIN})")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Number of LEDs (default: {DEFAULT_COUNT})")
    parser.add_argument("--brightness", type=float, default=DEFAULT_BRIGHTNESS, help=f"Brightness 0.0-1.0 (default: {DEFAULT_BRIGHTNESS})")
    args = parser.parse_args()
    
    # Map pin number to board pin
    pixel_pin = getattr(board, f"D{args.pin}")
    
    # Initialize the NeoPixels
    pixels = neopixel.NeoPixel(
        pixel_pin, 
        args.count, 
        brightness=args.brightness, 
        auto_write=False, 
        pixel_order=neopixel.GRB
    )
    
    try:
        print("NeoPixel Example")
        print(f"Pin: {args.pin}, LEDs: {args.count}, Brightness: {args.brightness}")
        
        # Clear all pixels
        pixels.fill((0, 0, 0))
        pixels.show()
        
        print("\\nDemo 1: Color Wipe")
        color_wipe(pixels, (255, 0, 0), 0.05)  # Red wipe
        color_wipe(pixels, (0, 255, 0), 0.05)  # Green wipe
        color_wipe(pixels, (0, 0, 255), 0.05)  # Blue wipe
        
        print("\\nDemo 2: Theater Chase")
        theater_chase(pixels, (127, 127, 127), 0.05)  # White chase
        theater_chase(pixels, (255, 0, 0), 0.05)      # Red chase
        theater_chase(pixels, (0, 0, 255), 0.05)      # Blue chase
        
        print("\\nDemo 3: Rainbow")
        rainbow(pixels, 0.01)
        
        print("\\nDemo 4: Rainbow Cycle")
        rainbow_cycle(pixels, 0.01)
        
        # Clear all pixels
        pixels.fill((0, 0, 0))
        pixels.show()
        
        print("\\nExample completed successfully!")
        return 0
    except KeyboardInterrupt:
        # Clear all pixels on Ctrl+C
        pixels.fill((0, 0, 0))
        pixels.show()
        print("\\nExample interrupted by user")
        return 0
    except Exception as e:
        print(f"\\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    try:
        with open("/tmp/neopixel_example.py", "w") as f:
            f.write(example_script)
        
        run_command(["sudo", "cp", "/tmp/neopixel_example.py", "/usr/local/bin/neopixel_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/neopixel_example.py"])
        
        logger.info("Created example script at /usr/local/bin/neopixel_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def create_config_file(pin: int = 18, count: int = 16) -> bool:
    """Create a configuration file for NeoPixel settings."""
    logger.info("Creating NeoPixel configuration file...")
    
    config_content = f"""# NeoPixel Configuration
PIN={pin}
COUNT={count}
BRIGHTNESS=0.2
"""
    
    try:
        with open("/tmp/neopixel_config", "w") as f:
            f.write(config_content)
        
        run_command(["sudo", "cp", "/tmp/neopixel_config", "/etc/neopixel_config"])
        
        logger.info("Created configuration file at /etc/neopixel_config")
        return True
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="NeoPixel LED Setup and Test Script")
    parser.add_argument("--pin", type=int, default=18, help="GPIO pin number connected to the NeoPixel data line (default: 18)")
    parser.add_argument("--count", type=int, default=16, help="Number of NeoPixel LEDs in the strip/ring (default: 16)")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without requiring physical hardware")
    args = parser.parse_args()
    
    # Set simulation mode
    global SIMULATION_MODE
    SIMULATION_MODE = args.simulation
    
    if SIMULATION_MODE:
        logger.info("Running in simulation mode - no physical hardware required")
    
    logger.info("Starting NeoPixel setup...")
    
    # Install dependencies
    setup_neopixel_libraries()
    
    # Configure system
    configure_system_for_neopixel()
    
    # Test NeoPixel
    neopixel_working = test_neopixel(args.pin, args.count)
    
    # Create example script
    create_example_script(args.pin, args.count)
    
    # Create configuration file
    create_config_file(args.pin, args.count)
    
    # Print summary
    logger.info("\n=== NeoPixel Setup Summary ===")
    logger.info(f"GPIO Pin: {args.pin}")
    logger.info(f"LED Count: {args.count}")
    logger.info(f"NeoPixel Test: {'Successful' if neopixel_working or SIMULATION_MODE else 'Failed'}")
    
    if not neopixel_working and not SIMULATION_MODE:
        logger.warning("NeoPixel test failed. Please check the following:")
        logger.info("1. Make sure the NeoPixel strip is properly connected to the GPIO pin")
        logger.info("2. Check the power connection to the NeoPixel strip")
        logger.info("3. If using GPIO18, make sure audio is disabled in /boot/config.txt")
        logger.info("4. Try a different GPIO pin (e.g., GPIO10, GPIO12, GPIO21)")
        logger.info("5. Verify that the LED count is correct")
        logger.info("6. Try running this script again after checking the connections")
    else:
        logger.info("\nNeoPixel setup completed successfully!")
        logger.info("You can run the example script with: sudo neopixel_example.py")
        logger.info("To use different settings: sudo neopixel_example.py --pin 10 --count 30 --brightness 0.5")
    
    return 0 if neopixel_working or SIMULATION_MODE else 1

if __name__ == "__main__":
    sys.exit(main())
