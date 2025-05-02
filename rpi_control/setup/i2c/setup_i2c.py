#!/usr/bin/env python3
"""
I2C Setup Script for Raspberry Pi

This script installs all necessary dependencies and configures the system
for working with I2C devices on the Raspberry Pi.

Usage:
  python3 setup_i2c.py [--force-reboot]

Options:
  --force-reboot  Reboot the Pi if configuration changes require it
"""

import os
import sys
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
    "system": ["i2c-tools", "python3-smbus", "libi2c-dev", "python3-pip", "python3-dev"],
    "python": ["smbus2", "adafruit-blinka"]
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
    
    return i2c_addresses

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
    """Create an example script for using I2C."""
    logger.info("Creating example script...")
    
    example_script = """#!/usr/bin/env python3
'''
I2C Example Script

This script demonstrates how to use I2C devices on the Raspberry Pi.
'''

import time
import sys
import smbus2

def main():
    try:
        # Initialize the I2C bus
        bus = smbus2.SMBus(1)  # Use bus 1 for newer Raspberry Pi models
        
        print("I2C Example Script")
        print("Scanning for I2C devices...")
        
        # Scan for I2C devices
        devices_found = []
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                devices_found.append(addr)
                print(f"Found device at address: 0x{addr:02X}")
            except Exception:
                pass
        
        if not devices_found:
            print("No I2C devices found")
            return 1
        
        # Example: Read from the first device found
        device_addr = devices_found[0]
        print(f"\\nReading from device at address 0x{device_addr:02X}...")
        
        try:
            # Try to read the first register
            value = bus.read_byte_data(device_addr, 0x00)
            print(f"Value at register 0x00: 0x{value:02X}")
            
            # Try to read multiple registers
            values = bus.read_i2c_block_data(device_addr, 0x00, 10)
            print("Values at registers 0x00-0x09:")
            for i, val in enumerate(values):
                print(f"  Register 0x{i:02X}: 0x{val:02X}")
        except Exception as e:
            print(f"Error reading from device: {e}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Close the I2C bus
        try:
            bus.close()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
"""
    
    try:
        # Create the example script
        with open("/tmp/i2c_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        run_command(["sudo", "cp", "/tmp/i2c_example.py", "/usr/local/bin/i2c_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/i2c_example.py"])
        
        logger.info("Created example script at /usr/local/bin/i2c_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="I2C Setup Script for Raspberry Pi")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    logger.info("Starting I2C setup...")
    
    # Install dependencies
    if not install_dependencies():
        logger.warning("Some dependencies could not be installed")
    
    # Ensure I2C is enabled
    i2c_enabled = ensure_i2c_enabled()
    
    if not i2c_enabled:
        logger.error("Failed to enable I2C. Please enable it manually using 'sudo raspi-config'.")
        return 1
    
    # Create I2C device files if they don't exist
    create_i2c_devices()
    
    # Detect I2C devices
    i2c_addresses = detect_i2c_devices()
    
    # Create example script
    create_example_script()
    
    # Print summary
    logger.info("\n=== I2C Setup Summary ===")
    logger.info(f"I2C Enabled: {'Yes' if i2c_enabled else 'No'}")
    logger.info(f"I2C Devices Found: {len(i2c_addresses)}")
    
    if i2c_addresses:
        logger.info("Found I2C devices at addresses:")
        for addr in i2c_addresses:
            logger.info(f"  0x{addr:02X}")
        logger.info("I2C is working correctly!")
        logger.info("You can run the example script with: i2c_example.py")
    else:
        logger.warning("No I2C devices were found.")
        logger.info("This could be because:")
        logger.info("1. No I2C devices are connected")
        logger.info("2. The I2C devices are not properly connected")
        logger.info("3. The I2C bus needs to be restarted")
    
    # Reboot if required and --force-reboot is specified
    if args.force_reboot:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0 if i2c_enabled else 1

if __name__ == "__main__":
    sys.exit(main())
