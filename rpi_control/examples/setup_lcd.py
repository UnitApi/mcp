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
  python3 setup_lcd.py [--force-reboot]

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
    
    # Check if I2C device files exist
    i2c_devices_exist = os.path.exists("/dev/i2c-1") or os.path.exists("/dev/i2c-0")
    
    if i2c_devices_exist:
        logger.info("I2C device files already exist")
        return True
    
    # Create I2C device files
    try:
        # Try to create /dev/i2c-1
        run_command(["sudo", "mknod", "-m", "0660", "/dev/i2c-1", "c", "89", "1"], check=False)
        run_command(["sudo", "chgrp", "i2c", "/dev/i2c-1"], check=False)
        
        # Try to create /dev/i2c-0
        run_command(["sudo", "mknod", "-m", "0660", "/dev/i2c-0", "c", "89", "0"], check=False)
        run_command(["sudo", "chgrp", "i2c", "/dev/i2c-0"], check=False)
        
        logger.info("Created I2C device files")
        return True
    except Exception as e:
        logger.error(f"Failed to create I2C device files: {e}")
        return False

def detect_i2c_devices() -> List[int]:
    """
    Detect I2C devices connected to the Raspberry Pi.
    Returns a list of I2C addresses found.
    """
    logger.info("Detecting I2C devices...")
    i2c_addresses = []
    
    # Method 1: Use i2cdetect command
    if shutil.which("i2cdetect"):
        for bus_num in [1, 0]:  # Try bus 1 first, then bus 0
            returncode, stdout, stderr = run_command(
                ["i2cdetect", "-y", str(bus_num)],
                check=False
            )
            
            if returncode == 0:
                logger.info(f"Successfully ran i2cdetect on bus {bus_num}")
                
                # Parse the output to find I2C addresses
                for line in stdout.splitlines()[1:]:  # Skip the header line
                    if line.startswith(' '):
                        parts = line.split(':')
                        if len(parts) > 1:
                            row = parts[1].strip()
                            row_base = int(parts[0].strip(), 16) * 16
                            for i, val in enumerate(row.split()):
                                if val != "--":
                                    addr = row_base + i
                                    i2c_addresses.append(addr)
                                    logger.info(f"Found I2C device at address: 0x{addr:02X}")
                
                if i2c_addresses:
                    break  # Stop if we found devices
            else:
                logger.debug(f"i2cdetect failed on bus {bus_num}: {stderr}")
    else:
        logger.warning("i2cdetect command not found, installing...")
        run_command(["sudo", "apt-get", "update"], check=False)
        run_command(["sudo", "apt-get", "install", "-y", "i2c-tools"], check=False)
        
        # Try again after installing
        for bus_num in [1, 0]:
            returncode, stdout, stderr = run_command(
                ["i2cdetect", "-y", str(bus_num)],
                check=False
            )
            
            if returncode == 0:
                logger.info(f"Successfully ran i2cdetect on bus {bus_num}")
                
                # Parse the output to find I2C addresses
                for line in stdout.splitlines()[1:]:
                    if line.startswith(' '):
                        parts = line.split(':')
                        if len(parts) > 1:
                            row = parts[1].strip()
                            row_base = int(parts[0].strip(), 16) * 16
                            for i, val in enumerate(row.split()):
                                if val != "--":
                                    addr = row_base + i
                                    i2c_addresses.append(addr)
                                    logger.info(f"Found I2C device at address: 0x{addr:02X}")
                
                if i2c_addresses:
                    break
    
    # Method 2: Use Python's smbus or smbus2
    if not i2c_addresses:
        logger.info("Trying to detect I2C devices with Python...")
        
        # Install smbus if needed
        run_command(["sudo", "apt-get", "install", "-y", "python3-smbus"], check=False)
        run_command([sys.executable, "-m", "pip", "install", "--user", "smbus2"], check=False)
        
        # Try with smbus
        try:
            import smbus
            
            for bus_num in [1, 0]:
                try:
                    bus = smbus.SMBus(bus_num)
                    logger.info(f"Successfully opened SMBus {bus_num}")
                    
                    # Scan all possible I2C addresses
                    for addr in range(0x03, 0x78):
                        try:
                            bus.read_byte(addr)
                            i2c_addresses.append(addr)
                            logger.info(f"Found I2C device at address: 0x{addr:02X}")
                        except Exception:
                            pass
                    
                    bus.close()
                    
                    if i2c_addresses:
                        break
                except Exception as e:
                    logger.debug(f"Error using SMBus {bus_num}: {e}")
        except ImportError:
            logger.warning("smbus module not available")
            
            # Try with smbus2
            try:
                import smbus2
                
                for bus_num in [1, 0]:
                    try:
                        bus = smbus2.SMBus(bus_num)
                        logger.info(f"Successfully opened SMBus2 {bus_num}")
                        
                        # Scan all possible I2C addresses
                        for addr in range(0x03, 0x78):
                            try:
                                bus.read_byte(addr)
                                i2c_addresses.append(addr)
                                logger.info(f"Found I2C device at address: 0x{addr:02X}")
                            except Exception:
                                pass
                        
                        bus.close()
                        
                        if i2c_addresses:
                            break
                    except Exception as e:
                        logger.debug(f"Error using SMBus2 {bus_num}: {e}")
            except ImportError:
                logger.warning("smbus2 module not available")
    
    if not i2c_addresses:
        # If no devices found, add common LCD addresses to try anyway
        logger.warning("No I2C devices found. Adding common LCD addresses to try...")
        common_lcd_addresses = [0x27, 0x3F, 0x20, 0x38]
        for addr in common_lcd_addresses:
            logger.info(f"Adding common LCD address: 0x{addr:02X}")
            i2c_addresses.append(addr)
    
    return i2c_addresses

def setup_lcd_libraries() -> bool:
    """Install and set up LCD libraries."""
    logger.info("Setting up LCD libraries...")
    
    # Install RPLCD library
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "install", "--user", "RPLCD"],
        check=False
    )
    
    if returncode == 0:
        logger.info("Successfully installed RPLCD library")
        return True
    else:
        logger.error(f"Failed to install RPLCD library: {stderr}")
        
        # Try with sudo
        returncode, stdout, stderr = run_command(
            ["sudo", sys.executable, "-m", "pip", "install", "RPLCD"],
            check=False
        )
        
        if returncode == 0:
            logger.info("Successfully installed RPLCD library with sudo")
            return True
        else:
            logger.error(f"Failed to install RPLCD library with sudo: {stderr}")
            return False

def test_lcd_display(address: int = 0x27) -> bool:
    """
    Test the LCD display at the given I2C address.
    Returns True if the test is successful, False otherwise.
    """
    logger.info(f"Testing LCD display at address 0x{address:02X}...")
    
    # Common LCD types to try
    lcd_types = [
        {"i2c_expander": "PCF8574", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "PCF8574", "cols": 20, "rows": 4, "charmap": "A00"},
        {"i2c_expander": "PCF8574A", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "PCF8574A", "cols": 20, "rows": 4, "charmap": "A00"},
        {"i2c_expander": "MCP23008", "cols": 16, "rows": 2, "charmap": "A00"},
        {"i2c_expander": "MCP23008", "cols": 20, "rows": 4, "charmap": "A00"},
    ]
    
    try:
        # Try to import RPLCD library
        from RPLCD.i2c import CharLCD
        
        # Try each LCD type
        for lcd_config in lcd_types:
            try:
                logger.info(f"Trying LCD with config: {lcd_config}")
                lcd = CharLCD(
                    i2c_expander=lcd_config["i2c_expander"],
                    address=address,
                    cols=lcd_config["cols"],
                    rows=lcd_config["rows"],
                    charmap=lcd_config["charmap"]
                )
                
                # Clear the display
                lcd.clear()
                
                # Display test message
                lcd.write_string("LCD Test")
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"Addr: 0x{address:02X}")
                
                # Display configuration information
                logger.info(f"Successfully initialized LCD at 0x{address:02X}")
                logger.info(f"Type: {lcd_config['i2c_expander']}")
                logger.info(f"Size: {lcd_config['cols']}x{lcd_config['rows']}")
                
                # Wait a bit before clearing
                time.sleep(3)
                
                # Display more information
                lcd.clear()
                lcd.write_string(f"{lcd_config['i2c_expander']}")
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"{lcd_config['cols']}x{lcd_config['rows']}")
                
                time.sleep(3)
                
                # Clean up
                lcd.clear()
                lcd.close()
                
                # Save the successful configuration
                with open("/home/pi/lcd_config.txt", "w") as f:
                    f.write(f"LCD_TYPE={lcd_config['i2c_expander']}\n")
                    f.write(f"LCD_ADDRESS=0x{address:02X}\n")
                    f.write(f"LCD_COLS={lcd_config['cols']}\n")
                    f.write(f"LCD_ROWS={lcd_config['rows']}\n")
                    f.write(f"LCD_CHARMAP={lcd_config['charmap']}\n")
                
                logger.info(f"Saved LCD configuration to /home/pi/lcd_config.txt")
                
                return True
            except Exception as e:
                logger.warning(f"Failed with config {lcd_config}: {e}")
        
        logger.error("All LCD configurations failed")
        return False
    
    except ImportError:
        logger.error("RPLCD library not available. Install with: pip install RPLCD")
        return False
    except Exception as e:
        logger.error(f"Error testing LCD: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="LCD Setup and Test Script")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    logger.info("Starting LCD setup and test...")
    
    # Step 1: Ensure I2C is enabled
    i2c_enabled = ensure_i2c_enabled()
    
    if not i2c_enabled:
        logger.error("Failed to enable I2C. Please enable it manually using 'sudo raspi-config'.")
        return 1
    
    # Step 2: Create I2C device files if they don't exist
    create_i2c_devices()
    
    # Step 3: Set up LCD libraries
    setup_lcd_libraries()
    
    # Step 4: Detect I2C devices
    i2c_addresses = detect_i2c_devices()
    
    # Step 5: Test LCD for each address found
    lcd_found = False
    
    if i2c_addresses:
        for addr in i2c_addresses:
            if test_lcd_display(addr):
                logger.info(f"Successfully tested LCD at address 0x{addr:02X}")
                lcd_found = True
                break
    
    # Print summary
    logger.info("\n=== LCD Setup Summary ===")
    logger.info(f"I2C Enabled: {'Yes' if i2c_enabled else 'No'}")
    logger.info(f"LCD Found and Tested: {'Yes' if lcd_found else 'No'}")
    
    if lcd_found:
        logger.info("LCD is working correctly!")
    else:
        logger.warning("LCD was not found or could not be initialized.")
        logger.info("Please check the following:")
        logger.info("1. Make sure the LCD is properly connected to the I2C pins (SDA and SCL)")
        logger.info("2. Check the power connection to the LCD")
        logger.info("3. Verify that the I2C address is correct (commonly 0x27 or 0x3F)")
        logger.info("4. Try running this script again after checking the connections")
    
    # Reboot if required and --force-reboot is specified
    if args.force_reboot:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0 if lcd_found else 1

if __name__ == "__main__":
    sys.exit(main())
