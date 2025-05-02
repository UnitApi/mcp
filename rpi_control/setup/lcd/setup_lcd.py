#!/usr/bin/env python3
"""
LCD Setup and Test Script

This script specifically focuses on setting up and testing an LCD display
connected to a Raspberry Pi via I2C. It will:

1. Ensure I2C is properly enabled and configured
2. Load necessary kernel modules
3. Fix common I2C permission issues
4. Detect connected LCD displays
5. Test the LCD with a simple message

Usage:
  python3 setup_lcd.py [--force-reboot] [--simulation]

Options:
  --force-reboot  Reboot the Pi if configuration changes require it
  --simulation    Run in simulation mode without requiring physical hardware
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

def ensure_i2c_enabled() -> bool:
    """Ensure I2C is enabled in the Raspberry Pi configuration."""
    logger.info("Ensuring I2C is enabled...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming I2C is enabled")
        return True
    
    # Check if I2C is enabled in config.txt
    i2c_enabled_in_config = False
    try:
        with open("/boot/config.txt", "r") as f:
            config = f.read()
            if "dtparam=i2c_arm=on" in config:
                i2c_enabled_in_config = True
                logger.info("I2C is enabled in /boot/config.txt")
            else:
                logger.warning("I2C is not enabled in /boot/config.txt")
                
                # Enable I2C in config.txt
                logger.info("Enabling I2C in /boot/config.txt...")
                returncode, stdout, stderr = run_command(
                    ["sudo", "raspi-config", "nonint", "do_i2c", "0"],
                    check=False
                )
                
                if returncode == 0:
                    logger.info("Successfully enabled I2C using raspi-config")
                    i2c_enabled_in_config = True
                else:
                    logger.warning(f"Failed to enable I2C using raspi-config: {stderr}")
                    
                    # Try manual method
                    try:
                        # Backup config.txt
                        run_command(["sudo", "cp", "/boot/config.txt", "/boot/config.txt.bak"])
                        
                        # Add I2C configuration
                        run_command([
                            "sudo", "bash", "-c",
                            "echo '\n# Enable I2C interface\ndtparam=i2c_arm=on' >> /boot/config.txt"
                        ])
                        
                        logger.info("Manually added I2C configuration to /boot/config.txt")
                        i2c_enabled_in_config = True
                    except Exception as e:
                        logger.error(f"Failed to manually enable I2C: {e}")
    except Exception as e:
        logger.error(f"Could not check/modify config.txt: {e}")
    
    # Load I2C kernel modules
    load_i2c_modules()
    
    # Fix I2C permissions
    fix_i2c_permissions()
    
    return i2c_enabled_in_config

def load_i2c_modules() -> bool:
    """Load I2C kernel modules."""
    logger.info("Loading I2C kernel modules...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming I2C modules are loaded")
        return True
    
    # Load i2c-dev module
    returncode1, stdout1, stderr1 = run_command(["sudo", "modprobe", "i2c-dev"], check=False)
    
    # Load i2c-bcm2708 or i2c-bcm2835 module (depending on Pi version)
    returncode2, stdout2, stderr2 = run_command(["sudo", "modprobe", "i2c-bcm2708"], check=False)
    if returncode2 != 0:
        returncode2, stdout2, stderr2 = run_command(["sudo", "modprobe", "i2c-bcm2835"], check=False)
    
    # Add modules to /etc/modules for persistence
    try:
        modules_to_add = ["i2c-dev", "i2c-bcm2835"]
        modules_content = ""
        
        try:
            with open("/etc/modules", "r") as f:
                modules_content = f.read()
        except:
            pass
        
        new_modules = []
        for module in modules_to_add:
            if module not in modules_content:
                new_modules.append(module)
        
        if new_modules:
            with open("/tmp/new_modules", "w") as f:
                f.write(modules_content)
                for module in new_modules:
                    f.write(f"{module}\n")
            
            run_command(["sudo", "cp", "/tmp/new_modules", "/etc/modules"])
            logger.info("Added I2C modules to /etc/modules for persistence")
    except Exception as e:
        logger.warning(f"Could not update /etc/modules: {e}")
    
    # Check if modules are loaded
    returncode, stdout, stderr = run_command(["lsmod"], check=False)
    if "i2c_bcm" in stdout or "i2c_dev" in stdout:
        logger.info("I2C kernel modules are loaded")
        return True
    else:
        logger.warning("I2C kernel modules are not loaded")
        return False

def fix_i2c_permissions() -> bool:
    """Fix I2C permissions."""
    logger.info("Fixing I2C permissions...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming I2C permissions are correct")
        return True
    
    # Create/update udev rule for I2C
    udev_rule = 'KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0660"'
    
    try:
        # Create i2c group if it doesn't exist
        returncode, stdout, stderr = run_command(
            ["getent", "group", "i2c"],
            check=False
        )
        
        if returncode != 0:
            logger.info("Creating i2c group...")
            run_command(["sudo", "groupadd", "-f", "i2c"])
        
        # Add current user to i2c group
        current_user = os.environ.get("USER", "pi")
        logger.info(f"Adding user {current_user} to i2c group...")
        run_command(["sudo", "usermod", "-aG", "i2c", current_user])
        
        # Create udev rule
        with open("/tmp/99-i2c-permissions.rules", "w") as f:
            f.write(udev_rule)
        
        run_command([
            "sudo", "cp", "/tmp/99-i2c-permissions.rules",
            "/etc/udev/rules.d/99-i2c-permissions.rules"
        ])
        
        # Reload udev rules
        run_command(["sudo", "udevadm", "control", "--reload-rules"])
        run_command(["sudo", "udevadm", "trigger"])
        
        logger.info("Fixed I2C permissions")
        return True
    except Exception as e:
        logger.error(f"Failed to fix I2C permissions: {e}")
        return False

def create_i2c_devices() -> bool:
    """Create I2C device files if they don't exist."""
    logger.info("Creating I2C device files...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Assuming I2C device files exist")
        return True
    
    # Check if I2C device files exist
    if os.path.exists("/dev/i2c-1"):
        logger.info("I2C device files already exist")
        return True
    
    # Create I2C device files
    try:
        run_command(["sudo", "mknod", "/dev/i2c-0", "c", "89", "0"])
        run_command(["sudo", "mknod", "/dev/i2c-1", "c", "89", "1"])
        run_command(["sudo", "chmod", "660", "/dev/i2c-0"])
        run_command(["sudo", "chmod", "660", "/dev/i2c-1"])
        run_command(["sudo", "chown", "root:i2c", "/dev/i2c-0"])
        run_command(["sudo", "chown", "root:i2c", "/dev/i2c-1"])
        
        logger.info("Created I2C device files")
        return True
    except Exception as e:
        logger.error(f"Failed to create I2C device files: {e}")
        return False

def detect_i2c_devices() -> List[str]:
    """Detect I2C devices connected to the Raspberry Pi."""
    logger.info("Detecting I2C devices...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Adding simulated LCD at address 0x27")
        return ["0x27"]
    
    # Check if i2cdetect is installed
    returncode, stdout, stderr = run_command(["which", "i2cdetect"], check=False)
    if returncode != 0:
        logger.warning("i2cdetect command not found, installing...")
        run_command(["sudo", "apt-get", "update"], check=False)
        run_command(["sudo", "apt-get", "install", "-y", "i2c-tools"], check=False)
    
    # Run i2cdetect to find I2C devices
    returncode, stdout, stderr = run_command(["sudo", "i2cdetect", "-y", "1"], check=False)
    
    # Parse output to find device addresses
    devices = []
    if returncode == 0:
        for line in stdout.split("\n"):
            if ":" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    row = parts[0].strip()
                    for i, val in enumerate(parts[1].strip().split()):
                        if val != "--":
                            col = i
                            addr = f"0x{row}{val}"
                            devices.append(addr)
    
    # If no devices found, try Python method
    if not devices:
        logger.info("Trying to detect I2C devices with Python...")
        try:
            # Try to import smbus
            import_smbus = run_command([sys.executable, "-c", "import smbus"], check=False)
            if import_smbus[0] != 0:
                logger.info("Installing smbus...")
                run_command(["sudo", "apt-get", "install", "-y", "python3-smbus"], check=False)
            
            # Try to detect devices
            for addr in range(0x03, 0x78):
                detect_cmd = f"""
import smbus
try:
    bus = smbus.SMBus(1)
    bus.read_byte({addr})
    print('Device found at 0x{addr:02x}')
except Exception:
    pass
"""
                returncode, stdout, stderr = run_command([sys.executable, "-c", detect_cmd], check=False)
                if "Device found" in stdout:
                    devices.append(f"0x{addr:02x}")
        except Exception as e:
            logger.warning(f"Failed to detect I2C devices with Python: {e}")
    
    # If still no devices found, add common LCD addresses to try
    if not devices:
        logger.warning("No I2C devices found. Adding common LCD addresses to try...")
        common_addresses = ["0x27", "0x3F", "0x20", "0x38"]
        for addr in common_addresses:
            logger.info(f"Adding common LCD address: {addr}")
            devices.append(addr)
    
    if devices:
        logger.info(f"Found I2C devices: {', '.join(devices)}")
    else:
        logger.warning("No I2C devices found")
    
    return devices

def setup_lcd_libraries() -> bool:
    """Install and set up LCD libraries."""
    logger.info("Installing dependencies...")
    
    # Update package lists
    logger.info("Updating package lists...")
    run_command(["sudo", "apt-get", "update"], check=False)
    
    # Install system packages
    system_packages = ["i2c-tools", "python3-smbus", "libi2c-dev", "python3-pip", "python3-dev"]
    for package in system_packages:
        logger.info(f"Checking if system package '{package}' is installed...")
        returncode, stdout, stderr = run_command(["dpkg", "-s", package], check=False)
        if returncode != 0:
            logger.info(f"Installing system package '{package}'...")
            run_command(["sudo", "apt-get", "install", "-y", package], check=False)
    
    # Install Python packages
    python_packages = ["RPLCD", "smbus2", "adafruit-circuitpython-charlcd"]
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
    
    return True

def test_lcd_display(address: str = "0x27") -> bool:
    """Test the LCD display at the given I2C address."""
    logger.info(f"Testing LCD display at address {address}...")
    
    if SIMULATION_MODE:
        logger.info("Simulation mode: Simulating successful LCD test")
        return True
    
    # Convert address string to int if needed
    if isinstance(address, str):
        address = int(address, 16)
    
    # Try different LCD configurations
    configs = [
        {"i2c_expander": "PCF8574", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "PCF8574", "cols": 20, "rows": 4, "charmap": "A00"},
        {"i2c_expander": "PCF8574A", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "PCF8574A", "cols": 20, "rows": 4, "charmap": "A00"},
        {"i2c_expander": "MCP23008", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "MCP23008", "cols": 20, "rows": 4, "charmap": "A00"},
    ]
    
    for config in configs:
        logger.info(f"Trying LCD with config: {config}")
        
        test_script = f"""
from RPLCD.i2c import CharLCD
import time

try:
    lcd = CharLCD(
        i2c_expander='{config["i2c_expander"]}',
        address={address},
        cols={config["cols"]},
        rows={config["rows"]},
        charmap='{config["charmap"]}'
    )
    
    lcd.clear()
    lcd.write_string('LCD Test')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('Success!')
    time.sleep(2)
    lcd.clear()
    lcd.write_string('Setup Complete')
    time.sleep(1)
    lcd.clear()
    print('LCD test successful')
except Exception as e:
    print(f'Error: {{e}}')
    exit(1)
"""
        
        returncode, stdout, stderr = run_command([sys.executable, "-c", test_script], check=False)
        
        if returncode == 0 and "LCD test successful" in stdout:
            logger.info(f"LCD test successful with config: {config}")
            return True
        else:
            logger.warning(f"Failed with config {config}: {stderr}")
    
    logger.error("All LCD configurations failed")
    return False

def create_example_script() -> bool:
    """Create an example script for using the LCD display."""
    logger.info("Creating example script...")
    
    example_script = """#!/usr/bin/env python3
# LCD Example Script
# This script demonstrates how to use an LCD display with a Raspberry Pi

from RPLCD.i2c import CharLCD
import time
import sys

def main():
    # Common LCD addresses are 0x27 and 0x3F
    # Common LCD sizes are 16x2 and 20x4
    try:
        # Try with PCF8574 at 0x27 (16x2)
        lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)
        print("Connected to LCD at 0x27")
    except Exception as e:
        print(f"Error connecting to LCD at 0x27: {e}")
        try:
            # Try with PCF8574 at 0x3F (16x2)
            lcd = CharLCD('PCF8574', 0x3F, cols=16, rows=2)
            print("Connected to LCD at 0x3F")
        except Exception as e:
            print(f"Error connecting to LCD at 0x3F: {e}")
            print("Could not connect to LCD. Check connections and I2C address.")
            return
    
    try:
        # Clear the display
        lcd.clear()
        
        # Display a message
        lcd.write_string("Hello, World!")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("Raspberry Pi")
        
        # Wait 2 seconds
        time.sleep(2)
        
        # Display a scrolling message
        lcd.clear()
        message = "This is a scrolling message on the LCD display. "
        for i in range(len(message)):
            lcd.clear()
            lcd.write_string(message[i:i+16])
            time.sleep(0.3)
        
        # Display a countdown
        lcd.clear()
        lcd.write_string("Countdown:")
        for i in range(10, -1, -1):
            lcd.cursor_pos = (1, 0)
            lcd.write_string(f"{i:02d} seconds    ")
            time.sleep(1)
        
        # Display a final message
        lcd.clear()
        lcd.write_string("Example")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("Completed!")
        
        # Wait 2 seconds and clear
        time.sleep(2)
        lcd.clear()
        
        print("LCD example completed successfully!")
    except KeyboardInterrupt:
        lcd.clear()
        print("Example interrupted by user")
    except Exception as e:
        print(f"Error during example: {e}")

if __name__ == "__main__":
    main()
"""
    
    try:
        with open("/tmp/lcd_example.py", "w") as f:
            f.write(example_script)
        
        run_command(["sudo", "cp", "/tmp/lcd_example.py", "/usr/local/bin/lcd_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/lcd_example.py"])
        
        logger.info("Created example script at /usr/local/bin/lcd_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="LCD Setup and Test Script")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without requiring physical hardware")
    args = parser.parse_args()
    
    # Set simulation mode
    global SIMULATION_MODE
    SIMULATION_MODE = args.simulation
    
    if SIMULATION_MODE:
        logger.info("Running in simulation mode - no physical hardware required")
    
    logger.info("Starting LCD setup...")
    
    # Install dependencies
    setup_lcd_libraries()
    
    # Ensure I2C is enabled
    i2c_enabled = ensure_i2c_enabled()
    if not i2c_enabled and not SIMULATION_MODE:
        logger.error("Failed to enable I2C")
        return 1
    
    # Load I2C kernel modules
    load_i2c_modules()
    
    # Fix I2C permissions
    fix_i2c_permissions()
    
    # Create I2C device files
    create_i2c_devices()
    
    # Detect I2C devices
    i2c_devices = detect_i2c_devices()
    
    # Test LCD display
    lcd_found = False
    for device in i2c_devices:
        if test_lcd_display(device):
            lcd_found = True
            break
    
    # Create example script
    create_example_script()
    
    # Print summary
    logger.info("\n=== LCD Setup Summary ===")
    logger.info(f"I2C Enabled: {'Yes' if i2c_enabled or SIMULATION_MODE else 'No'}")
    logger.info(f"LCD Found and Tested: {'Yes' if lcd_found or SIMULATION_MODE else 'No'}")
    
    if not lcd_found and not SIMULATION_MODE:
        logger.warning("LCD was not found or could not be initialized.")
        logger.info("Please check the following:")
        logger.info("1. Make sure the LCD is properly connected to the I2C pins (SDA and SCL)")
        logger.info("2. Check the power connection to the LCD")
        logger.info("3. Verify that the I2C address is correct (commonly 0x27 or 0x3F)")
        logger.info("4. Try running this script again after checking the connections")
    
    # Reboot if required
    if args.force_reboot and not SIMULATION_MODE:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
