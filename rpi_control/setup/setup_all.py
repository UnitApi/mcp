#!/usr/bin/env python3
"""
Raspberry Pi Hardware Setup Master Script

This script serves as the main entry point for setting up all hardware components
on a Raspberry Pi. It provides options to set up individual components or all at once.

Usage:
  python3 setup_all.py [--component COMPONENT] [--all] [--force-reboot]

Options:
  --component COMPONENT  Set up a specific component (lcd, gpio, audio, i2c, spi, led_matrix, camera, sensors)
  --all                  Set up all components
  --force-reboot         Reboot the Pi if configuration changes require it
"""

import os
import sys
import argparse
import logging
import subprocess
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Define available components
AVAILABLE_COMPONENTS = [
    "lcd",
    "gpio",
    "audio",
    "i2c",
    "spi",
    "led_matrix",
    "camera",
    "sensors"
]

def run_command(cmd: List[str], check: bool = True) -> tuple:
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

def setup_component(component: str, force_reboot: bool = False) -> bool:
    """Set up a specific component."""
    if component not in AVAILABLE_COMPONENTS:
        logger.error(f"Unknown component: {component}")
        return False
    
    logger.info(f"Setting up {component}...")
    
    # Get the absolute path to the component's setup script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    setup_script = os.path.join(script_dir, component, f"setup_{component}.py")
    
    if not os.path.exists(setup_script):
        logger.error(f"Setup script for {component} not found: {setup_script}")
        return False
    
    # Run the component's setup script
    cmd = [sys.executable, setup_script]
    if force_reboot:
        cmd.append("--force-reboot")
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        logger.info(f"Successfully set up {component}")
        return True
    else:
        logger.error(f"Failed to set up {component}: {stderr}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Raspberry Pi Hardware Setup Master Script")
    parser.add_argument("--component", choices=AVAILABLE_COMPONENTS, help="Set up a specific component")
    parser.add_argument("--all", action="store_true", help="Set up all components")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    args = parser.parse_args()
    
    if not args.component and not args.all:
        parser.print_help()
        return 1
    
    # Set up a specific component
    if args.component:
        success = setup_component(args.component, args.force_reboot)
        return 0 if success else 1
    
    # Set up all components
    if args.all:
        logger.info("Setting up all components...")
        
        # Set up components in a specific order to handle dependencies
        # I2C should be first since many other components depend on it
        components_order = ["i2c", "spi", "gpio", "lcd", "led_matrix", "audio", "camera", "sensors"]
        
        success = True
        for component in components_order:
            component_success = setup_component(component, False)  # Don't reboot after each component
            if not component_success:
                success = False
        
        # Reboot at the end if needed and --force-reboot is specified
        if args.force_reboot:
            logger.info("Rebooting the Raspberry Pi...")
            run_command(["sudo", "reboot"])
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
