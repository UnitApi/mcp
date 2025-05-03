#!/usr/bin/env python3
"""
UnitMCP Base Runner

A standardized base runner for client-server examples in UnitMCP.
This provides a common framework for running examples with client-server architecture.
"""

import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BaseRunner:
    """
    Base runner for UnitMCP examples with client-server architecture.
    
    This class provides a standardized way to:
    - Load environment variables
    - Start server and client processes
    - Handle signals for graceful shutdown
    - Manage configuration
    
    It can be used as a base class for specific example runners or used directly.
    """
    
    def __init__(
        self,
        server_config_path: str,
        client_config_path: str,
        server_script_path: Optional[str] = None,
        client_script_path: Optional[str] = None
    ):
        """
        Initialize the base runner.
        
        Parameters
        ----------
        server_config_path : str
            Path to the server configuration file
        client_config_path : str
            Path to the client configuration file
        server_script_path : Optional[str]
            Path to the server script (defaults to "server.py" in the same directory)
        client_script_path : Optional[str]
            Path to the client script (defaults to "client.py" in the same directory)
        """
        self.server_config_path = server_config_path
        self.client_config_path = client_config_path
        
        # Set default script paths if not provided
        if server_script_path is None:
            self.server_script_path = os.path.join(os.path.dirname(__file__), "server.py")
        else:
            self.server_script_path = server_script_path
            
        if client_script_path is None:
            self.client_script_path = os.path.join(os.path.dirname(__file__), "client.py")
        else:
            self.client_script_path = client_script_path
        
        self.server_process = None
        self.client_process = None
        self.running = False
        
        # Load configurations
        self.server_config = self._load_config(self.server_config_path)
        self.client_config = self._load_config(self.client_config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load a configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
            
        Returns
        -------
        Dict[str, Any]
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return {}
    
    def start_server(self):
        """
        Start the server process.
        
        Returns
        -------
        bool
            True if the server was started successfully, False otherwise
        """
        try:
            logger.info(f"Starting server process from {self.server_script_path}...")
            
            # Start the server process
            self.server_process = subprocess.Popen(
                [sys.executable, self.server_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            
            logger.info(f"Server process started with PID {self.server_process.pid}")
            
            # Start threads to read server output
            import threading
            
            def read_server_output():
                for line in self.server_process.stdout:
                    print(f"[SERVER] {line.strip()}")
            
            def read_server_error():
                for line in self.server_process.stderr:
                    print(f"[SERVER ERROR] {line.strip()}")
            
            threading.Thread(target=read_server_output, daemon=True).start()
            threading.Thread(target=read_server_error, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting server process: {e}")
            return False
    
    def start_client(self):
        """
        Start the client process.
        
        Returns
        -------
        bool
            True if the client was started successfully, False otherwise
        """
        try:
            logger.info(f"Starting client process from {self.client_script_path}...")
            
            # Start the client process
            self.client_process = subprocess.Popen(
                [sys.executable, self.client_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            
            logger.info(f"Client process started with PID {self.client_process.pid}")
            
            # Start threads to read client output
            import threading
            
            def read_client_output():
                for line in self.client_process.stdout:
                    print(f"[CLIENT] {line.strip()}")
            
            def read_client_error():
                for line in self.client_process.stderr:
                    print(f"[CLIENT ERROR] {line.strip()}")
            
            threading.Thread(target=read_client_output, daemon=True).start()
            threading.Thread(target=read_client_error, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting client process: {e}")
            return False
    
    def stop_processes(self):
        """
        Stop the server and client processes.
        
        Returns
        -------
        bool
            True if all processes were stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping processes...")
            
            # Stop the client process
            if self.client_process and self.client_process.poll() is None:
                logger.info(f"Terminating client process (PID {self.client_process.pid})...")
                self.client_process.terminate()
                try:
                    self.client_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Client process did not terminate, killing...")
                    self.client_process.kill()
            
            # Stop the server process
            if self.server_process and self.server_process.poll() is None:
                logger.info(f"Terminating server process (PID {self.server_process.pid})...")
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Server process did not terminate, killing...")
                    self.server_process.kill()
            
            logger.info("All processes stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping processes: {e}")
            return False
    
    def run(self):
        """
        Run the example.
        
        This method:
        1. Sets up signal handlers for graceful shutdown
        2. Loads environment variables
        3. Starts the server process
        4. Waits for the server to start
        5. Starts the client process
        6. Waits for processes to finish
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            self.running = False
            self.stop_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Load environment variables
            try:
                from src.unitmcp.utils.env_loader import EnvLoader
                env_loader = EnvLoader()
                env_loader.load_env()
            except ImportError:
                logger.warning("EnvLoader not found, skipping environment loading")
            
            # Start the server process
            if not self.start_server():
                logger.error("Failed to start server process")
                return 1
            
            # Wait for the server to start
            logger.info("Waiting for server to start...")
            time.sleep(2)
            
            # Start the client process
            if not self.start_client():
                logger.error("Failed to start client process")
                self.stop_processes()
                return 1
            
            # Wait for processes to finish
            while self.running:
                # Check if processes are still running
                if self.server_process and self.server_process.poll() is not None:
                    logger.error(f"Server process exited with code {self.server_process.returncode}")
                    self.running = False
                    break
                
                if self.client_process and self.client_process.poll() is not None:
                    logger.error(f"Client process exited with code {self.client_process.returncode}")
                    self.running = False
                    break
                
                time.sleep(0.1)
            
            # Stop processes
            self.stop_processes()
            
            return 0
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self.stop_processes()
            return 0
        
        except Exception as e:
            logger.exception(f"Error in runner: {e}")
            self.stop_processes()
            return 1


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
        "--server-script",
        type=str,
        help="Path to the server script",
    )
    
    parser.add_argument(
        "--client-script",
        type=str,
        help="Path to the client script",
    )
    
    return parser.parse_args()


def main():
    """
    Main function to run the example.
    
    This function:
    1. Parses command-line arguments
    2. Creates a BaseRunner instance
    3. Runs the example
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set default configuration paths if not provided
    if args.server_config is None:
        server_config = os.path.join(os.path.dirname(__file__), "config", "server.yaml")
    else:
        server_config = args.server_config
    
    if args.client_config is None:
        client_config = os.path.join(os.path.dirname(__file__), "config", "client.yaml")
    else:
        client_config = args.client_config
    
    # Create and run the runner
    runner = BaseRunner(
        server_config_path=server_config,
        client_config_path=client_config,
        server_script_path=args.server_script,
        client_script_path=args.client_script,
    )
    
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
