#!/usr/bin/env python3
"""
Remote Setup Script for Raspberry Pi Hardware

This script copies the setup files to a Raspberry Pi and executes them remotely.
It handles the remote installation of necessary packages, configuration of hardware,
and testing of components.

Usage:
  python3 remote_setup.py --host HOSTNAME [--port PORT] [--user USERNAME] 
                         [--component COMPONENT] [--all] [--force-reboot]
                         [--simulation]

Options:
  --host HOSTNAME       Hostname or IP address of the Raspberry Pi
  --port PORT           SSH port (default: 22)
  --user USERNAME       SSH username (default: pi)
  --component COMPONENT Set up a specific component (lcd, gpio, i2c, spi, etc.)
  --all                 Set up all components
  --force-reboot        Reboot the Pi if configuration changes require it
  --simulation          Run in simulation mode without requiring physical hardware or sudo privileges
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple

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

def create_ssh_command(host: str, port: int, user: str, command: str) -> List[str]:
    """Create an SSH command to run on the remote host."""
    return ["ssh", f"{user}@{host}", "-p", str(port), command]

def create_scp_command(host: str, port: int, user: str, src: str, dst: str, recursive: bool = False) -> List[str]:
    """Create an SCP command to copy files to the remote host."""
    cmd = ["scp"]
    if recursive:
        cmd.append("-r")
    cmd.extend(["-P", str(port), src, f"{user}@{host}:{dst}"])
    return cmd

def check_ssh_connection(host: str, port: int, user: str) -> bool:
    """Check if SSH connection to the remote host is possible."""
    logger.info(f"Checking SSH connection to {user}@{host}:{port}...")
    
    cmd = create_ssh_command(host, port, user, "echo 'SSH connection successful'")
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode == 0:
        logger.info("SSH connection successful")
        return True
    else:
        logger.error(f"SSH connection failed: {stderr}")
        return False

def prepare_remote_directory(host: str, port: int, user: str) -> bool:
    """Prepare the remote directory for setup files."""
    logger.info("Preparing remote directory...")
    
    # Create setup directory on the remote host
    cmd = create_ssh_command(host, port, user, "mkdir -p ~/rpi_setup")
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode == 0:
        logger.info("Created remote setup directory")
        return True
    else:
        logger.error(f"Failed to create remote setup directory: {stderr}")
        return False

def copy_setup_files(host: str, port: int, user: str, component: Optional[str] = None) -> bool:
    """Copy setup files to the remote host."""
    logger.info("Copying setup files to the remote host...")
    
    # Get the absolute path to the setup directory
    setup_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to copy
    files_to_copy = [
        os.path.join(setup_dir, "setup_all.py"),
        os.path.join(setup_dir, "README.md")
    ]
    
    # If a specific component is specified, only copy that component's directory
    if component:
        if component not in AVAILABLE_COMPONENTS:
            logger.error(f"Unknown component: {component}")
            return False
        
        component_dir = os.path.join(setup_dir, component)
        if os.path.exists(component_dir):
            # Copy the component directory
            cmd = create_scp_command(host, port, user, component_dir, "~/rpi_setup/", recursive=True)
            returncode, stdout, stderr = run_command(cmd, check=False)
            
            if returncode != 0:
                logger.error(f"Failed to copy component directory: {stderr}")
                return False
        else:
            logger.error(f"Component directory not found: {component_dir}")
            return False
    else:
        # Copy all component directories
        for comp in AVAILABLE_COMPONENTS:
            component_dir = os.path.join(setup_dir, comp)
            if os.path.exists(component_dir):
                # Copy the component directory
                cmd = create_scp_command(host, port, user, component_dir, "~/rpi_setup/", recursive=True)
                returncode, stdout, stderr = run_command(cmd, check=False)
                
                if returncode != 0:
                    logger.error(f"Failed to copy component directory {comp}: {stderr}")
                    return False
    
    # Copy main setup files
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            cmd = create_scp_command(host, port, user, file_path, "~/rpi_setup/")
            returncode, stdout, stderr = run_command(cmd, check=False)
            
            if returncode != 0:
                logger.error(f"Failed to copy file {file_path}: {stderr}")
                return False
    
    logger.info("Successfully copied setup files to the remote host")
    return True

def run_remote_setup(host: str, port: int, user: str, component: Optional[str] = None, all_components: bool = False, force_reboot: bool = False, simulation: bool = False) -> bool:
    """Run the setup script on the remote host."""
    logger.info("Running setup script on the remote host...")
    
    # Build the command to run on the remote host
    remote_cmd = "cd ~/rpi_setup && "
    
    if component:
        # Run setup for a specific component
        remote_cmd += f"python3 {component}/setup_{component}.py"
    elif all_components:
        # Run setup for all components
        remote_cmd += "python3 setup_all.py --all"
    else:
        logger.error("No component specified and --all not set")
        return False
    
    # Add force-reboot option if specified
    if force_reboot:
        remote_cmd += " --force-reboot"
    
    # Add simulation mode if specified
    if simulation:
        remote_cmd += " --simulation"
        logger.info("Running in simulation mode - no physical hardware or sudo privileges required")
    
    # Set AUTO_YES environment variable to automatically continue without sudo
    # Use proper SSH syntax for setting environment variables
    remote_cmd = f"cd ~/rpi_setup && AUTO_YES=1 python3 {remote_cmd.replace('cd ~/rpi_setup && python3 ', '')}"
    
    # Run the command on the remote host
    cmd = create_ssh_command(host, port, user, remote_cmd)
    logger.info(f"Executing remote command: {' '.join(cmd)}")
    
    # For this command, we want to show the output in real-time
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        returncode = process.wait()
        
        if returncode == 0:
            logger.info("Remote setup completed successfully")
            return True
        else:
            logger.error(f"Remote setup failed with exit code {returncode}")
            return False
    except Exception as e:
        logger.error(f"Error running remote setup: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Remote Setup Script for Raspberry Pi Hardware")
    parser.add_argument("--host", required=True, help="Hostname or IP address of the Raspberry Pi")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--user", default="pi", help="SSH username (default: pi)")
    parser.add_argument("--component", choices=AVAILABLE_COMPONENTS, help="Set up a specific component")
    parser.add_argument("--all", action="store_true", help="Set up all components")
    parser.add_argument("--force-reboot", action="store_true", help="Reboot the Pi if configuration changes require it")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without requiring physical hardware or sudo privileges")
    args = parser.parse_args()
    
    # Check if component or --all is specified
    if not args.component and not args.all:
        logger.error("Either --component or --all must be specified")
        parser.print_help()
        return 1
    
    # Check SSH connection
    if not check_ssh_connection(args.host, args.port, args.user):
        return 1
    
    # Prepare remote directory
    if not prepare_remote_directory(args.host, args.port, args.user):
        return 1
    
    # Copy setup files
    if not copy_setup_files(args.host, args.port, args.user, args.component if not args.all else None):
        return 1
    
    # Run remote setup
    if not run_remote_setup(args.host, args.port, args.user, args.component, args.all, args.force_reboot, args.simulation):
        return 1
    
    logger.info("Remote setup completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
