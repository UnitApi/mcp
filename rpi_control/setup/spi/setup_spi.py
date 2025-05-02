#!/usr/bin/env python3
"""
SPI Setup Script for Raspberry Pi

This script installs all necessary dependencies and configures the system
for working with SPI devices on the Raspberry Pi.

Usage:
  python3 setup_spi.py [--force-reboot]

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
    "system": ["python3-dev", "python3-pip", "python3-spidev"],
    "python": ["spidev", "adafruit-blinka"]
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

def ensure_spi_enabled() -> bool:
    """Ensure SPI is enabled in the Raspberry Pi configuration."""
    logger.info("Ensuring SPI is enabled...")
    
    # Check if SPI is enabled in config.txt
    spi_enabled_in_config = False
    try:
        with open("/boot/config.txt", "r") as f:
            config = f.read()
            if "dtparam=spi=on" in config:
                spi_enabled_in_config = True
                logger.info("SPI is enabled in /boot/config.txt")
            else:
                logger.warning("SPI is not enabled in /boot/config.txt")
                
                # Enable SPI in config.txt
                logger.info("Enabling SPI in /boot/config.txt...")
                returncode, stdout, stderr = run_command(
                    ["sudo", "raspi-config", "nonint", "do_spi", "0"],
                    check=False
                )
                
                if returncode == 0:
                    logger.info("Successfully enabled SPI using raspi-config")
                    spi_enabled_in_config = True
                else:
                    logger.warning(f"Failed to enable SPI using raspi-config: {stderr}")
                    
                    # Try manual method
                    try:
                        # Backup config.txt
                        run_command(["sudo", "cp", "/boot/config.txt", "/boot/config.txt.bak"])
                        
                        # Add SPI configuration
                        run_command([
                            "sudo", "bash", "-c",
                            "echo '\n# Enable SPI interface\ndtparam=spi=on' >> /boot/config.txt"
                        ])
                        
                        logger.info("Manually added SPI configuration to /boot/config.txt")
                        spi_enabled_in_config = True
                    except Exception as e:
                        logger.error(f"Failed to manually enable SPI: {e}")
    except Exception as e:
        logger.error(f"Could not check/modify config.txt: {e}")
    
    # Load SPI kernel modules
    load_spi_modules()
    
    # Fix SPI permissions
    fix_spi_permissions()
    
    return spi_enabled_in_config

def load_spi_modules() -> bool:
    """Load SPI kernel modules."""
    logger.info("Loading SPI kernel modules...")
    
    # Load spi-bcm2835 module
    returncode, stdout, stderr = run_command(["sudo", "modprobe", "spi-bcm2835"], check=False)
    
    # Load spidev module
    returncode2, stdout2, stderr2 = run_command(["sudo", "modprobe", "spidev"], check=False)
    
    # Add modules to /etc/modules for persistence
    try:
        modules_to_add = ["spi-bcm2835", "spidev"]
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
            logger.info("Added SPI modules to /etc/modules for persistence")
    except Exception as e:
        logger.warning(f"Could not update /etc/modules: {e}")
    
    # Check if modules are loaded
    returncode, stdout, stderr = run_command(["lsmod"], check=False)
    if "spi_bcm2835" in stdout or "spidev" in stdout:
        logger.info("SPI kernel modules are loaded")
        return True
    else:
        logger.warning("SPI kernel modules are not loaded")
        return False

def fix_spi_permissions() -> bool:
    """Fix SPI permissions."""
    logger.info("Fixing SPI permissions...")
    
    # Create/update udev rule for SPI
    udev_rule = 'KERNEL=="spidev*", GROUP="spi", MODE="0660"'
    
    try:
        # Create spi group if it doesn't exist
        returncode, stdout, stderr = run_command(
            ["getent", "group", "spi"],
            check=False
        )
        
        if returncode != 0:
            logger.info("Creating spi group...")
            run_command(["sudo", "groupadd", "-f", "spi"])
        
        # Add current user to spi group
        current_user = os.environ.get("USER", "pi")
        logger.info(f"Adding user {current_user} to spi group...")
        run_command(["sudo", "usermod", "-aG", "spi", current_user])
        
        # Create udev rule
        with open("/tmp/99-spi-permissions.rules", "w") as f:
            f.write(udev_rule)
        
        run_command([
            "sudo", "cp", "/tmp/99-spi-permissions.rules",
            "/etc/udev/rules.d/99-spi-permissions.rules"
        ])
        
        # Reload udev rules
        run_command(["sudo", "udevadm", "control", "--reload-rules"])
        run_command(["sudo", "udevadm", "trigger"])
        
        logger.info("Fixed SPI permissions")
        return True
    except Exception as e:
        logger.error(f"Failed to fix SPI permissions: {e}")
        return False

def check_spi_devices() -> bool:
    """Check if SPI device files exist."""
    logger.info("Checking SPI devices...")
    
    # Check if SPI device files exist
    spi_devices_exist = os.path.exists("/dev/spidev0.0") or os.path.exists("/dev/spidev0.1")
    
    if spi_devices_exist:
        logger.info("SPI device files exist")
        return True
    else:
        logger.warning("SPI device files do not exist")
        return False

def test_spi() -> bool:
    """Test SPI functionality."""
    logger.info("Testing SPI functionality...")
    
    try:
        # Try to import spidev
        import spidev
        
        # Open SPI device
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        
        # Configure SPI
        spi.max_speed_hz = 1000000  # 1MHz
        spi.mode = 0
        
        # Try to transfer some data
        logger.info("Trying to transfer data over SPI...")
        response = spi.xfer2([0x00, 0x00])
        
        # Close SPI device
        spi.close()
        
        logger.info(f"SPI transfer successful, received: {response}")
        return True
    except ImportError:
        logger.error("spidev library not available. Install with: pip install spidev")
        return False
    except Exception as e:
        logger.error(f"Error testing SPI: {e}")
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
    """Create an example script for using SPI."""
    logger.info("Creating example script...")
    
    example_script = """#!/usr/bin/env python3
'''
SPI Example Script

This script demonstrates how to use SPI devices on the Raspberry Pi.
It reads data from an SPI device (like an ADC) and prints the values.
'''

import time
import sys
import spidev

def main():
    try:
        # Initialize the SPI bus
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        
        # Configure SPI
        spi.max_speed_hz = 1000000  # 1MHz
        spi.mode = 0
        
        print("SPI Example Script")
        print("Reading from SPI device...")
        print("Press Ctrl+C to exit")
        
        # Main loop
        while True:
            # Read from SPI device
            # This example assumes an ADC like MCP3008
            # Command format: [start bit, single/diff, channel (3 bits), don't care]
            # For channel 0 in single-ended mode: 0b1000 0000 0000 0000 = 0x8000
            resp = spi.xfer2([0x01, 0x80, 0x00])
            
            # Process the response
            # For MCP3008: 10-bit value is in the last 10 bits of the response
            value = ((resp[1] & 0x03) << 8) + resp[2]
            
            # Print the value
            print(f"SPI Value: {value}")
            
            # Wait before next reading
            time.sleep(0.5)
        
        return 0
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Close the SPI bus
        try:
            spi.close()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
"""
    
    try:
        # Create the example script
        with open("/tmp/spi_example.py", "w") as f:
            f.write(example_script)
        
        # Copy to /usr/local/bin and make executable
        run_command(["sudo", "cp", "/tmp/spi_example.py", "/usr/local/bin/spi_example.py"])
        run_command(["sudo", "chmod", "+x", "/usr/local/bin/spi_example.py"])
        
        logger.info("Created example script at /usr/local/bin/spi_example.py")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="SPI Setup Script for Raspberry Pi")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    logger.info("Starting SPI setup...")
    
    # Install dependencies
    if not install_dependencies():
        logger.warning("Some dependencies could not be installed")
    
    # Ensure SPI is enabled
    spi_enabled = ensure_spi_enabled()
    
    if not spi_enabled:
        logger.error("Failed to enable SPI. Please enable it manually using 'sudo raspi-config'.")
        return 1
    
    # Check SPI devices
    spi_devices_exist = check_spi_devices()
    
    # Test SPI functionality
    spi_works = test_spi()
    
    # Create example script
    create_example_script()
    
    # Print summary
    logger.info("\n=== SPI Setup Summary ===")
    logger.info(f"SPI Enabled: {'Yes' if spi_enabled else 'No'}")
    logger.info(f"SPI Devices Exist: {'Yes' if spi_devices_exist else 'No'}")
    logger.info(f"SPI Test: {'Passed' if spi_works else 'Failed'}")
    
    if spi_works:
        logger.info("SPI is working correctly!")
        logger.info("You can run the example script with: spi_example.py")
    else:
        logger.warning("SPI could not be initialized or tested.")
        logger.info("This could be because:")
        logger.info("1. No SPI devices are connected")
        logger.info("2. The SPI devices are not properly connected")
        logger.info("3. The system needs to be rebooted")
    
    # Reboot if required and --force-reboot is specified
    if args.force_reboot:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0 if spi_enabled else 1

if __name__ == "__main__":
    sys.exit(main())
