#!/usr/bin/env python3
"""
Object Recognition Runner

This script sets up and runs both the client and server components
of the object recognition example.
"""

import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.unitmcp.utils.env_loader import EnvLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ObjectRecognitionRunner:
    """
    Runner for the object recognition example.
    
    This class handles:
    - Loading environment variables
    - Starting the server process
    - Starting the client process
    - Handling signals for graceful shutdown
    """
    
    def __init__(self, server_config_path: str, client_config_path: str):
        """
        Initialize the object recognition runner.
        
        Parameters
        ----------
        server_config_path : str
            Path to the server configuration file
        client_config_path : str
            Path to the client configuration file
        """
        self.server_config_path = server_config_path
        self.client_config_path = client_config_path
        self.server_process = None
        self.client_process = None
        self.running = False
    
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
            Configuration
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def start_server(self):
        """Start the server process."""
        logger.info("Starting server process...")
        
        # Get the server script path
        server_script = os.path.join(os.path.dirname(__file__), "server.py")
        
        # Start the server process
        self.server_process = subprocess.Popen(
            [sys.executable, server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        logger.info(f"Server process started with PID {self.server_process.pid}")
        
        # Start a thread to read server output
        import threading
        
        def read_server_output():
            for line in self.server_process.stdout:
                print(f"[SERVER] {line.strip()}")
        
        def read_server_error():
            for line in self.server_process.stderr:
                print(f"[SERVER ERROR] {line.strip()}")
        
        threading.Thread(target=read_server_output, daemon=True).start()
        threading.Thread(target=read_server_error, daemon=True).start()
    
    def start_client(self):
        """Start the client process."""
        logger.info("Starting client process...")
        
        # Get the client script path
        client_script = os.path.join(os.path.dirname(__file__), "client.py")
        
        # Start the client process
        self.client_process = subprocess.Popen(
            [sys.executable, client_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        logger.info(f"Client process started with PID {self.client_process.pid}")
        
        # Start a thread to read client output
        import threading
        
        def read_client_output():
            for line in self.client_process.stdout:
                print(f"[CLIENT] {line.strip()}")
        
        def read_client_error():
            for line in self.client_process.stderr:
                print(f"[CLIENT ERROR] {line.strip()}")
        
        threading.Thread(target=read_client_output, daemon=True).start()
        threading.Thread(target=read_client_error, daemon=True).start()
    
    def stop_processes(self):
        """Stop the server and client processes."""
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
    
    def run(self):
        """Run the object recognition example."""
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
            env_loader = EnvLoader()
            env_loader.load_env()
            
            # Start the server process
            self.start_server()
            
            # Wait for the server to start
            import time
            time.sleep(2)
            
            # Start the client process
            self.start_client()
            
            # Wait for processes to finish
            while self.running:
                # Check if processes are still running
                if self.server_process.poll() is not None:
                    logger.error(f"Server process exited with code {self.server_process.returncode}")
                    self.running = False
                    break
                
                if self.client_process.poll() is not None:
                    logger.error(f"Client process exited with code {self.client_process.returncode}")
                    self.running = False
                    break
                
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.exception(f"Error in runner: {e}")
        
        finally:
            # Stop processes
            self.stop_processes()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Object Recognition Runner")
    
    parser.add_argument(
        "--server-config",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config", "server.yaml"),
        help="Path to the server configuration file",
    )
    
    parser.add_argument(
        "--client-config",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config", "client.yaml"),
        help="Path to the client configuration file",
    )
    
    return parser.parse_args()


def main():
    """Run the object recognition example."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Create and run the runner
    runner = ObjectRecognitionRunner(args.server_config, args.client_config)
    runner.run()


if __name__ == "__main__":
    main()
