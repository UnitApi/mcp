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
    # Basic interfaces
    "i2c",
    "spi",
    "gpio",
    "uart",
    "pwm",
    
    # Display components
    "lcd",
    "oled",
    "led_matrix",
    
    # Input/Output devices
    "servo",
    "stepper",
    "relay",
    "neopixel",
    
    # Sensors
    "temperature",
    "pressure",
    "humidity",
    "motion",
    "distance",
    "accelerometer",
    "gyroscope",
    "rfid",
    
    # Other peripherals
    "camera",
    "audio",
    "adc",
    "dac",
    "rtc",
    
    # Wireless interfaces
    "bluetooth",
    "wifi"
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
        logger.warning(f"Setup script for {component} not found: {setup_script}")
        logger.info(f"Creating a placeholder setup script for {component}...")
        
        # Create component directory if it doesn't exist
        component_dir = os.path.join(script_dir, component)
        if not os.path.exists(component_dir):
            os.makedirs(component_dir)
        
        # Create a placeholder setup script
        create_placeholder_setup_script(component, setup_script)
        
        if not os.path.exists(setup_script):
            logger.error(f"Failed to create placeholder setup script for {component}")
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

def create_placeholder_setup_script(component: str, script_path: str) -> bool:
    """Create a placeholder setup script for a component."""
    try:
        script_content = f"""#!/usr/bin/env python3
\"\"\"
{component.title()} Setup Script for Raspberry Pi (Placeholder)

This is a placeholder setup script for the {component} component.
It will be replaced with a full implementation in the future.

Usage:
  python3 setup_{component}.py [--force-reboot]

Options:
  --force-reboot  Reboot the Pi if configuration changes require it
\"\"\"

import os
import sys
import time
import logging
import argparse
import subprocess
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    \"\"\"Run a command and return the exit code, stdout, and stderr.\"\"\"
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

def create_example_script() -> bool:
    \"\"\"Create an example script for using {component}.\"\"\"
    logger.info("Creating example script for {component}...")
    
    # Define the example script content
    example_script = \"\"\"#!/usr/bin/env python3
# {component.title()} Example Script
# This script demonstrates how to use {component} with a Raspberry Pi

import time
import sys

def main():
    print("This is a placeholder example for {component}")
    print("A full implementation will be added in the future")
    
    # Simulate some activity
    for i in range(5):
        print(f"Simulating {component} operation... {{i+1}}/5")
        time.sleep(0.5)
    
    print("{component.title()} example completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\nExample interrupted by user")
        sys.exit(0)
\"\"\"
    
    # Create the example script file
    example_script_path = f"/usr/local/bin/{component}_example.py"
    try:
        with open(f"/tmp/{component}_example.py", "w") as f:
            f.write(example_script)
        
        # Copy the file to /usr/local/bin and make it executable
        cmd = ["sudo", "cp", f"/tmp/{component}_example.py", example_script_path]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode != 0:
            logger.error(f"Failed to copy example script: {{stderr}}")
            return False
        
        cmd = ["sudo", "chmod", "+x", example_script_path]
        returncode, stdout, stderr = run_command(cmd, check=False)
        
        if returncode != 0:
            logger.error(f"Failed to make example script executable: {{stderr}}")
            return False
        
        logger.info(f"Example script created at {{example_script_path}}")
        return True
    except Exception as e:
        logger.error(f"Failed to create example script: {{e}}")
        return False

def main():
    \"\"\"Main function.\"\"\"
    parser = argparse.ArgumentParser(description="{component.title()} Setup Script for Raspberry Pi (Placeholder)")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without hardware")
    args = parser.parse_args()
    
    # Create example script
    create_example_script()
    
    logger.info(f"Placeholder setup for {component} completed successfully")
    logger.info(f"A full implementation will be added in the future")
    
    # Reboot if required
    if args.force_reboot:
        logger.info("Rebooting the Raspberry Pi...")
        run_command(["sudo", "reboot"])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create placeholder setup script: {e}")
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
        # Basic interfaces should be first since many other components depend on them
        components_order = [
            # Basic interfaces first
            "i2c", "spi", "gpio", "uart", "pwm",
            
            # Then hardware that depends on these interfaces
            "lcd", "oled", "led_matrix", "servo", "stepper", "relay",
            "neopixel", "temperature", "pressure", "humidity", "motion",
            "distance", "accelerometer", "gyroscope", "rfid", "camera",
            "audio", "adc", "dac", "rtc",
            
            # Wireless interfaces last
            "bluetooth", "wifi"
        ]
        
        success = True
        for component in components_order:
            if component in AVAILABLE_COMPONENTS:  # Only try to set up components that are available
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
