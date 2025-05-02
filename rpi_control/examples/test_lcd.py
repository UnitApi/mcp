#!/usr/bin/env python3
"""
LCD Detection and Test Script

This script detects connected I2C LCD displays and tests them
by displaying text.
"""

import sys
import time
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def detect_i2c_devices() -> List[int]:
    """
    Detect I2C devices connected to the Raspberry Pi.
    Returns a list of I2C addresses found.
    """
    logger.info("Detecting I2C devices...")
    i2c_addresses = []
    
    try:
        # Try to use i2cdetect command
        result = subprocess.run(
            ["i2cdetect", "-y", "1"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            # Parse the output to find I2C addresses
            for line in result.stdout.splitlines()[1:]:  # Skip the header line
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
            logger.warning(f"i2cdetect command failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error detecting I2C devices: {e}")
    
    # If no devices found with i2cdetect, try with Python's smbus
    if not i2c_addresses:
        logger.info("Trying to detect I2C devices with SMBus...")
        try:
            import smbus
            bus = smbus.SMBus(1)  # Use I2C bus 1
            
            # Scan all possible I2C addresses
            for addr in range(0x03, 0x78):
                try:
                    bus.read_byte(addr)
                    i2c_addresses.append(addr)
                    logger.info(f"Found I2C device at address: 0x{addr:02X}")
                except Exception:
                    pass
            
            bus.close()
        except Exception as e:
            logger.error(f"Error using SMBus: {e}")
            
            # Try with smbus2 if smbus fails
            try:
                import smbus2
                bus = smbus2.SMBus(1)  # Use I2C bus 1
                
                # Scan all possible I2C addresses
                for addr in range(0x03, 0x78):
                    try:
                        bus.read_byte(addr)
                        i2c_addresses.append(addr)
                        logger.info(f"Found I2C device at address: 0x{addr:02X}")
                    except Exception:
                        pass
                
                bus.close()
            except Exception as e:
                logger.error(f"Error using SMBus2: {e}")
    
    return i2c_addresses

def test_lcd_display(address: int = 0x27) -> bool:
    """
    Test the LCD display at the given I2C address.
    Returns True if the test is successful, False otherwise.
    """
    logger.info(f"Testing LCD display at address 0x{address:02X}...")
    
    try:
        # Try to import RPLCD library
        from RPLCD.i2c import CharLCD
        
        # Common LCD types to try
        lcd_types = [
            {"i2c_expander": "PCF8574", "cols": 16, "rows": 2, "charmap": "A00"},
            {"i2c_expander": "PCF8574", "cols": 20, "rows": 4, "charmap": "A00"},
            {"i2c_expander": "PCF8574A", "cols": 16, "rows": 2, "charmap": "A00"},
            {"i2c_expander": "PCF8574A", "cols": 20, "rows": 4, "charmap": "A00"},
            {"i2c_expander": "MCP23008", "cols": 16, "rows": 2, "charmap": "A00"},
            {"i2c_expander": "MCP23008", "cols": 20, "rows": 4, "charmap": "A00"},
        ]
        
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
    logger.info("Starting LCD detection and test...")
    
    # Check if I2C is enabled
    try:
        with open("/boot/config.txt", "r") as f:
            config = f.read()
            if "dtparam=i2c_arm=on" in config:
                logger.info("I2C is enabled in /boot/config.txt")
            else:
                logger.warning("I2C might not be enabled in /boot/config.txt")
    except Exception as e:
        logger.warning(f"Could not check if I2C is enabled: {e}")
    
    # Detect I2C devices
    i2c_addresses = detect_i2c_devices()
    
    if not i2c_addresses:
        logger.warning("No I2C devices found. Check connections and ensure I2C is enabled.")
        logger.info("Trying default LCD address 0x27 anyway...")
        i2c_addresses = [0x27]  # Try the default address anyway
    
    # Test LCD for each address found
    success = False
    for addr in i2c_addresses:
        if test_lcd_display(addr):
            logger.info(f"Successfully tested LCD at address 0x{addr:02X}")
            success = True
            break
    
    if not success:
        logger.error("Failed to initialize any LCD display")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
