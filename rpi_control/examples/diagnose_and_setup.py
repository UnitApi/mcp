#!/usr/bin/env python3
"""
Raspberry Pi Hardware Diagnostic and Setup Script

This script performs comprehensive diagnostics on a Raspberry Pi's hardware setup,
focusing on I2C, GPIO, LCD displays, and other components. It will:

1. Check for required dependencies and install them if missing
2. Verify hardware interfaces are properly enabled
3. Detect connected I2C devices
4. Test LCD displays
5. Check GPIO access
6. Verify audio devices
7. Test LED matrix functionality

Usage:
  python3 diagnose_and_setup.py [--install] [--force-reboot]

Options:
  --install       Automatically install missing dependencies
  --force-reboot  Reboot the Pi if configuration changes require it
"""

import argparse
import os
import sys
import time
import logging
import subprocess
import shutil
from typing import List, Dict, Any, Optional, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Define required packages
REQUIRED_PACKAGES = {
    "system": ["i2c-tools", "python3-pip", "python3-dev", "python3-smbus", "libi2c-dev"],
    "python": ["RPLCD", "smbus2", "RPi.GPIO", "adafruit-blinka"]
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

def check_i2c_enabled() -> bool:
    """Check if I2C is enabled in the Raspberry Pi configuration."""
    logger.info("Checking if I2C is enabled...")
    
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
    except Exception as e:
        logger.warning(f"Could not check if I2C is enabled in config.txt: {e}")
    
    # Check if I2C modules are loaded
    i2c_modules_loaded = False
    returncode, stdout, stderr = run_command(["lsmod"], check=False)
    if "i2c_bcm" in stdout or "i2c_dev" in stdout:
        i2c_modules_loaded = True
        logger.info("I2C kernel modules are loaded")
    else:
        logger.warning("I2C kernel modules are not loaded")
    
    # Check if I2C device files exist
    i2c_devices_exist = os.path.exists("/dev/i2c-1") or os.path.exists("/dev/i2c-0")
    if i2c_devices_exist:
        logger.info("I2C device files exist")
    else:
        logger.warning("I2C device files do not exist")
    
    return i2c_enabled_in_config and (i2c_modules_loaded or i2c_devices_exist)

def enable_i2c() -> bool:
    """Enable I2C in the Raspberry Pi configuration."""
    logger.info("Enabling I2C...")
    
    # Use raspi-config to enable I2C
    returncode, stdout, stderr = run_command(["sudo", "raspi-config", "nonint", "do_i2c", "0"])
    if returncode == 0:
        logger.info("Successfully enabled I2C using raspi-config")
        return True
    else:
        logger.error(f"Failed to enable I2C using raspi-config: {stderr}")
        
        # Try manual method if raspi-config fails
        try:
            # Backup config.txt
            shutil.copy("/boot/config.txt", "/boot/config.txt.bak")
            
            # Check if the line already exists
            with open("/boot/config.txt", "r") as f:
                config_lines = f.readlines()
            
            i2c_line_exists = any("dtparam=i2c_arm=on" in line for line in config_lines)
            
            if not i2c_line_exists:
                # Add the line to enable I2C
                with open("/boot/config.txt", "a") as f:
                    f.write("\n# Enable I2C interface\ndtparam=i2c_arm=on\n")
                
                logger.info("Added I2C configuration to /boot/config.txt")
                return True
            else:
                logger.info("I2C configuration already exists in /boot/config.txt")
                return True
        except Exception as e:
            logger.error(f"Failed to manually enable I2C: {e}")
            return False

def load_i2c_modules() -> bool:
    """Load I2C kernel modules."""
    logger.info("Loading I2C kernel modules...")
    
    # Load i2c-dev module
    returncode1, stdout1, stderr1 = run_command(["sudo", "modprobe", "i2c-dev"], check=False)
    
    # Load i2c-bcm2708 or i2c-bcm2835 module (depending on Pi version)
    returncode2, stdout2, stderr2 = run_command(["sudo", "modprobe", "i2c-bcm2708"], check=False)
    if returncode2 != 0:
        returncode2, stdout2, stderr2 = run_command(["sudo", "modprobe", "i2c-bcm2835"], check=False)
    
    if returncode1 == 0 or returncode2 == 0:
        logger.info("Successfully loaded I2C kernel modules")
        
        # Add modules to /etc/modules for persistence
        try:
            with open("/etc/modules", "r") as f:
                modules = f.read()
            
            modules_to_add = []
            if "i2c-dev" not in modules:
                modules_to_add.append("i2c-dev")
            if "i2c-bcm2708" not in modules and "i2c-bcm2835" not in modules:
                modules_to_add.append("i2c-bcm2835")
            
            if modules_to_add:
                with open("/tmp/modules", "w") as f:
                    f.write(modules)
                    for module in modules_to_add:
                        f.write(f"{module}\n")
                
                run_command(["sudo", "cp", "/tmp/modules", "/etc/modules"])
                logger.info("Added I2C modules to /etc/modules for persistence")
        except Exception as e:
            logger.warning(f"Could not update /etc/modules: {e}")
        
        return True
    else:
        logger.error(f"Failed to load I2C kernel modules: {stderr1}, {stderr2}")
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
        returncode, stdout, stderr = run_command(["i2cdetect", "-y", "1"], check=False)
        
        if returncode == 0:
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
        else:
            # Try bus 0 if bus 1 fails
            returncode, stdout, stderr = run_command(["i2cdetect", "-y", "0"], check=False)
            
            if returncode == 0:
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
            else:
                logger.warning(f"i2cdetect command failed: {stderr}")
    else:
        logger.warning("i2cdetect command not found")
    
    # Method 2: Use Python's smbus
    if not i2c_addresses:
        logger.info("Trying to detect I2C devices with SMBus...")
        try:
            # Try to import smbus
            import smbus
            
            # Try bus 1 first (most common)
            try:
                bus = smbus.SMBus(1)
                bus_num = 1
            except:
                # Try bus 0 if bus 1 fails
                bus = smbus.SMBus(0)
                bus_num = 0
            
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
        except ImportError:
            logger.warning("smbus module not available")
            
            # Try with smbus2 if smbus fails
            try:
                import smbus2
                
                # Try bus 1 first (most common)
                try:
                    bus = smbus2.SMBus(1)
                    bus_num = 1
                except:
                    # Try bus 0 if bus 1 fails
                    bus = smbus2.SMBus(0)
                    bus_num = 0
                
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
            except ImportError:
                logger.warning("smbus2 module not available")
            except Exception as e:
                logger.error(f"Error using SMBus2: {e}")
        except Exception as e:
            logger.error(f"Error using SMBus: {e}")
    
    if not i2c_addresses:
        logger.warning("No I2C devices found. Check connections and ensure I2C is enabled.")
    
    return i2c_addresses

def identify_lcd_type(address: int = 0x27) -> Dict[str, Any]:
    """
    Identify the type of LCD connected at the given I2C address.
    Returns a dictionary with LCD configuration if successful, empty dict otherwise.
    """
    logger.info(f"Identifying LCD type at address 0x{address:02X}...")
    
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
                
                # If we get here, the LCD was initialized successfully
                logger.info(f"Successfully initialized LCD at 0x{address:02X}")
                logger.info(f"Type: {lcd_config['i2c_expander']}")
                logger.info(f"Size: {lcd_config['cols']}x{lcd_config['rows']}")
                
                # Clean up
                lcd.close()
                
                return lcd_config
            except Exception as e:
                logger.debug(f"Failed with config {lcd_config}: {e}")
        
        logger.warning("All LCD configurations failed")
        return {}
    
    except ImportError:
        logger.error("RPLCD library not available. Install with: pip install RPLCD")
        return {}
    except Exception as e:
        logger.error(f"Error identifying LCD: {e}")
        return {}

def test_lcd_display(address: int = 0x27, lcd_config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test the LCD display at the given I2C address with the specified configuration.
    Returns True if the test is successful, False otherwise.
    """
    logger.info(f"Testing LCD display at address 0x{address:02X}...")
    
    if lcd_config is None:
        # Use default configuration
        lcd_config = {
            "i2c_expander": "PCF8574",
            "cols": 16,
            "rows": 2,
            "charmap": "A00"
        }
    
    try:
        # Try to import RPLCD library
        from RPLCD.i2c import CharLCD
        
        logger.info(f"Initializing LCD with config: {lcd_config}")
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
        
        logger.info("Displayed test message on LCD")
        
        # Wait a bit before displaying more information
        time.sleep(3)
        
        # Display configuration information
        lcd.clear()
        lcd.write_string(f"{lcd_config['i2c_expander']}")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{lcd_config['cols']}x{lcd_config['rows']}")
        
        logger.info("Displayed configuration on LCD")
        
        time.sleep(3)
        
        # Clean up
        lcd.clear()
        lcd.close()
        
        logger.info("LCD test completed successfully")
        return True
    
    except ImportError:
        logger.error("RPLCD library not available. Install with: pip install RPLCD")
        return False
    except Exception as e:
        logger.error(f"Error testing LCD: {e}")
        return False

def check_gpio_access() -> bool:
    """Check if GPIO access is available."""
    logger.info("Checking GPIO access...")
    
    # Check if GPIO directory exists
    if os.path.exists("/sys/class/gpio"):
        logger.info("GPIO directory exists")
    else:
        logger.warning("GPIO directory does not exist")
        return False
    
    # Try to use RPi.GPIO
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Test a safe GPIO pin (GPIO 18 is commonly used)
        pin = 18
        
        # Set up the pin as output
        GPIO.setup(pin, GPIO.OUT)
        
        # Toggle the pin
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pin, GPIO.LOW)
        
        # Clean up
        GPIO.cleanup(pin)
        
        logger.info("Successfully tested GPIO access")
        return True
    except ImportError:
        logger.error("RPi.GPIO library not available. Install with: pip install RPi.GPIO")
        return False
    except Exception as e:
        logger.error(f"Error testing GPIO access: {e}")
        return False

def check_audio_devices() -> bool:
    """Check if audio devices are available."""
    logger.info("Checking audio devices...")
    
    # Check if aplay command is available
    if shutil.which("aplay"):
        returncode, stdout, stderr = run_command(["aplay", "-l"], check=False)
        
        if returncode == 0 and "card" in stdout:
            logger.info("Audio devices found:")
            for line in stdout.splitlines():
                if "card" in line:
                    logger.info(f"  {line}")
            return True
        else:
            logger.warning("No audio devices found")
            return False
    else:
        logger.warning("aplay command not found")
        return False

def check_led_matrix() -> bool:
    """Check if LED matrix libraries are available."""
    logger.info("Checking LED matrix libraries...")
    
    # Check for luma.led_matrix package
    if check_python_package("luma.led_matrix"):
        logger.info("luma.led_matrix package is installed")
        return True
    else:
        logger.warning("luma.led_matrix package is not installed")
        return False

def install_missing_dependencies(auto_install: bool = False) -> Tuple[bool, bool]:
    """
    Check for and install missing dependencies.
    Returns a tuple of (all_dependencies_installed, reboot_required).
    """
    logger.info("Checking for missing dependencies...")
    
    all_installed = True
    reboot_required = False
    
    # Check system packages
    missing_system_packages = []
    for package in REQUIRED_PACKAGES["system"]:
        if not check_system_package(package):
            missing_system_packages.append(package)
            all_installed = False
    
    # Check Python packages
    missing_python_packages = []
    for package in REQUIRED_PACKAGES["python"]:
        if not check_python_package(package):
            missing_python_packages.append(package)
            all_installed = False
    
    # Check if I2C is enabled
    i2c_enabled = check_i2c_enabled()
    if not i2c_enabled:
        all_installed = False
    
    # Install missing dependencies if auto_install is True
    if not all_installed and auto_install:
        logger.info("Installing missing dependencies...")
        
        # Install missing system packages
        if missing_system_packages:
            logger.info(f"Installing missing system packages: {', '.join(missing_system_packages)}")
            
            # Update package lists
            run_command(["sudo", "apt-get", "update"])
            
            # Install packages
            for package in missing_system_packages:
                install_system_package(package)
        
        # Install missing Python packages
        if missing_python_packages:
            logger.info(f"Installing missing Python packages: {', '.join(missing_python_packages)}")
            
            for package in missing_python_packages:
                install_python_package(package)
        
        # Enable I2C if not enabled
        if not i2c_enabled:
            logger.info("Enabling I2C...")
            
            if enable_i2c():
                reboot_required = True
            
            # Load I2C modules
            load_i2c_modules()
    
    return all_installed, reboot_required

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Raspberry Pi Hardware Diagnostic and Setup Script")
    parser.add_argument("--install", action="store_true", help="Automatically install missing dependencies")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    logger.info("Starting hardware diagnostics...")
    
    # Check for and install missing dependencies
    all_dependencies_installed, reboot_required = install_missing_dependencies(args.install)
    
    if not all_dependencies_installed and not args.install:
        logger.warning("Some dependencies are missing. Run with --install to install them.")
    
    # Check if I2C is enabled
    i2c_enabled = check_i2c_enabled()
    
    if not i2c_enabled:
        logger.warning("I2C is not enabled. Run with --install to enable it.")
    else:
        # Detect I2C devices
        i2c_addresses = detect_i2c_devices()
        
        # Test LCD for each address found
        lcd_found = False
        lcd_config = None
        
        if i2c_addresses:
            for addr in i2c_addresses:
                # Try to identify LCD type
                lcd_config = identify_lcd_type(addr)
                
                if lcd_config:
                    logger.info(f"Found LCD at address 0x{addr:02X} with config: {lcd_config}")
                    lcd_found = True
                    
                    # Test the LCD
                    if test_lcd_display(addr, lcd_config):
                        logger.info(f"Successfully tested LCD at address 0x{addr:02X}")
                    else:
                        logger.warning(f"Failed to test LCD at address 0x{addr:02X}")
                    
                    break
        
        if not lcd_found:
            logger.warning("No LCD found. Trying default address 0x27...")
            
            # Try the default address
            lcd_config = identify_lcd_type(0x27)
            
            if lcd_config:
                logger.info(f"Found LCD at default address 0x27 with config: {lcd_config}")
                
                # Test the LCD
                if test_lcd_display(0x27, lcd_config):
                    logger.info("Successfully tested LCD at default address 0x27")
                    lcd_found = True
                else:
                    logger.warning("Failed to test LCD at default address 0x27")
            else:
                logger.warning("No LCD found at default address 0x27")
    
    # Check GPIO access
    gpio_access = check_gpio_access()
    
    # Check audio devices
    audio_devices = check_audio_devices()
    
    # Check LED matrix
    led_matrix = check_led_matrix()
    
    # Print summary
    logger.info("\n=== Diagnostic Summary ===")
    logger.info(f"I2C Enabled: {'Yes' if i2c_enabled else 'No'}")
    logger.info(f"LCD Found: {'Yes' if lcd_found else 'No'}")
    if lcd_found and lcd_config:
        logger.info(f"LCD Type: {lcd_config['i2c_expander']}")
        logger.info(f"LCD Size: {lcd_config['cols']}x{lcd_config['rows']}")
    logger.info(f"GPIO Access: {'Yes' if gpio_access else 'No'}")
    logger.info(f"Audio Devices: {'Yes' if audio_devices else 'No'}")
    logger.info(f"LED Matrix Libraries: {'Yes' if led_matrix else 'No'}")
    
    # Reboot if required
    if reboot_required and (args.force_reboot or args.install):
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    elif reboot_required:
        logger.warning("A reboot is required for changes to take effect. Run with --force-reboot to reboot automatically.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
