#!/usr/bin/env python3
"""
UnitMCP Example Template - Runner

This module implements a template runner for UnitMCP examples.
It provides a standardized way to start and manage both client and server
components of an example.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

# Import the base runner
try:
    from examples.runner.base_runner import BaseRunner
except ImportError:
    # If we can't import directly, try a relative import
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from runner.base_runner import BaseRunner
    except ImportError:
        print("Error: Could not import BaseRunner. Make sure the runner module is in your Python path.")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ExampleRunner(BaseRunner):
    """
    Runner for the UnitMCP example.
    
    This class extends the BaseRunner to provide example-specific functionality.
    """
    
    def __init__(
        self,
        server_config_path=None,
        client_config_path=None,
        server_script_path=None,
        client_script_path=None
    ):
        """
        Initialize the example runner.
        
        Parameters
        ----------
        server_config_path : str, optional
            Path to the server configuration file
        client_config_path : str, optional
            Path to the client configuration file
        server_script_path : str, optional
            Path to the server script
        client_script_path : str, optional
            Path to the client script
        """
        # Set default paths relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if server_config_path is None:
            server_config_path = os.path.join(current_dir, "config", "server.yaml")
            
        if client_config_path is None:
            client_config_path = os.path.join(current_dir, "config", "client.yaml")
            
        if server_script_path is None:
            server_script_path = os.path.join(current_dir, "server.py")
            
        if client_script_path is None:
            client_script_path = os.path.join(current_dir, "client.py")
        
        # Initialize the base runner
        super().__init__(
            server_config_path=server_config_path,
            client_config_path=client_config_path,
            server_script_path=server_script_path,
            client_script_path=client_script_path
        )
        
        # Example-specific initialization can be added here
        logger.info("Example runner initialized")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Runner")
    
    parser.add_argument(
        "--server-config",
        type=str,
        help="Path to the server configuration file",
    )
    
    parser.add_argument(
        "--client-config",
        type=str,
        help="Path to the client configuration file",
    )
    
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Run only the server",
    )
    
    parser.add_argument(
        "--client-only",
        action="store_true",
        help="Run only the client",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser.parse_args()


def main():
    """
    Main function to run the example.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create the runner
    runner = ExampleRunner(
        server_config_path=args.server_config,
        client_config_path=args.client_config
    )
    
    # Run only the server if requested
    if args.server_only:
        if not runner.start_server():
            logger.error("Failed to start server")
            return 1
        
        # Wait for the server to finish
        try:
            while runner.server_process and runner.server_process.poll() is None:
                runner.server_process.wait()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            runner.stop_processes()
        
        return 0
    
    # Run only the client if requested
    if args.client_only:
        if not runner.start_client():
            logger.error("Failed to start client")
            return 1
        
        # Wait for the client to finish
        try:
            while runner.client_process and runner.client_process.poll() is None:
                runner.client_process.wait()
        except KeyboardInterrupt:
            logger.info("Client interrupted by user")
        finally:
            runner.stop_processes()
        
        return 0
    
    # Otherwise, run both client and server
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
