#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper script for UnitMCP that automatically installs required packages if they're missing.
"""

import os
import sys
import subprocess
import importlib.util
import time

def check_package_installed(package_name):
    """Check if a Python package is installed."""
    return importlib.util.find_spec(package_name) is not None

def install_package(package_path='.'):
    """Install the package from the current directory."""
    print(f"Installing UnitMCP package from {package_path}...")
    try:
        # Use pip to install the package in development mode
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', package_path])
        print("UnitMCP package installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing UnitMCP package: {e}")
        return False

def run_main_module():
    """Run the main UnitMCP orchestrator module."""
    try:
        # Import and run the main module
        from unitmcp.orchestrator.main import main
        main()
    except ImportError as e:
        print(f"Error importing UnitMCP module: {e}")
        sys.exit(1)

def main():
    """Main entry point for the wrapper script."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if unitmcp package is installed
    if not check_package_installed('unitmcp'):
        print("UnitMCP package not found. Attempting to install...")
        
        # Change to the script directory
        os.chdir(script_dir)
        
        # Install the package
        if install_package(script_dir):
            print("Waiting for installation to complete...")
            time.sleep(2)  # Give a moment for the installation to complete
        else:
            print("Failed to install UnitMCP package. Please install manually:")
            print(f"    pip install -e {script_dir}")
            sys.exit(1)
    
    # Run the main module
    run_main_module()

if __name__ == "__main__":
    main()
