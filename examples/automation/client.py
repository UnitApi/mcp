#!/usr/bin/env python3
"""
UnitMCP Example Template - Client

This module implements a template client for UnitMCP examples.
It provides a basic client implementation that can be extended
for specific example needs.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ExampleClient:
    """
    Template client implementation for UnitMCP examples.
    
    This class provides a basic client that:
    - Loads configuration from a YAML file
    - Connects to a server
    - Sends commands to the server
    - Processes responses
    - Provides a simple user interface
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the client with the given configuration.
        
        Parameters
        ----------
        config_path : str
            Path to the client configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        self.reader = None
        self.writer = None
        
        # Extract client settings from config
        client_config = self.config.get('client', {})
        self.name = client_config.get('name', 'example-client')
        self.client_id = client_config.get('id', 'client-001')
        
        # Extract connection settings from config
        connection_config = self.config.get('connection', {})
        self.server_host = connection_config.get('server_host', 'localhost')
        self.server_port = connection_config.get('server_port', 8000)
        self.timeout = connection_config.get('timeout', 30)
        self.retry_attempts = connection_config.get('retry_attempts', 3)
        self.retry_delay = connection_config.get('retry_delay', 5)
        
        # Extract UI settings from config
        ui_config = self.config.get('ui', {})
        self.ui_enabled = ui_config.get('enabled', True)
        self.ui_type = ui_config.get('type', 'console')
        self.ui_theme = ui_config.get('theme', 'default')
        self.ui_refresh_rate = ui_config.get('refresh_rate', 1.0)
        
        # Set up logging
        logging_config = self.config.get('logging', {})
        log_level = logging_config.get('level', 'info').upper()
        log_file = logging_config.get('file', '')
        log_format = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if hasattr(logging, log_level):
            logger.setLevel(getattr(logging, log_level))
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.
        
        Returns
        -------
        Dict[str, Any]
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            logger.error(f"Error loading configuration from {self.config_path}: {e}")
            return {}
    
    async def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns
        -------
        bool
            True if the connection was successful, False otherwise
        """
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Connecting to server at {self.server_host}:{self.server_port} (attempt {attempt + 1}/{self.retry_attempts})")
                
                self.reader, self.writer = await asyncio.open_connection(
                    self.server_host,
                    self.server_port
                )
                
                logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
                return True
                
            except ConnectionRefusedError:
                logger.warning(f"Connection refused by server at {self.server_host}:{self.server_port}")
                
            except Exception as e:
                logger.error(f"Error connecting to server: {e}")
                
            # Wait before retrying
            if attempt < self.retry_attempts - 1:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Failed to connect to server after {self.retry_attempts} attempts")
        return False
    
    async def disconnect(self):
        """
        Disconnect from the server.
        
        Returns
        -------
        bool
            True if the disconnection was successful, False otherwise
        """
        try:
            if self.writer:
                logger.info("Disconnecting from server...")
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass
                self.writer = None
                self.reader = None
                logger.info("Disconnected from server")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from server: {e}")
            return False
    
    async def send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a command to the server and get the response.
        
        Parameters
        ----------
        command : Dict[str, Any]
            Command to send to the server
            
        Returns
        -------
        Optional[Dict[str, Any]]
            Response from the server, or None if an error occurred
        """
        try:
            if not self.writer or not self.reader:
                logger.error("Not connected to server")
                return None
            
            # Add client information to the command
            command['client'] = {
                'name': self.name,
                'id': self.client_id
            }
            
            # Send the command
            logger.info(f"Sending command to server: {command}")
            self.writer.write(json.dumps(command).encode() + b'\n')
            await self.writer.drain()
            
            # Wait for response
            logger.info("Waiting for response from server...")
            response_data = await asyncio.wait_for(
                self.reader.readline(),
                timeout=self.timeout
            )
            
            if not response_data:
                logger.error("No response from server")
                return None
            
            # Parse the response
            try:
                response = json.loads(response_data.decode())
                logger.info(f"Received response from server: {response}")
                return response
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from server: {response_data.decode()}")
                return None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from server")
            return None
            
        except ConnectionResetError:
            logger.error(f"Connection reset by server")
            return None
            
        except Exception as e:
            logger.error(f"Error sending command to server: {e}")
            return None
    
    async def start(self):
        """
        Start the client.
        
        Returns
        -------
        bool
            True if the client was started successfully, False otherwise
        """
        try:
            logger.info("Starting client...")
            
            # Connect to the server
            if not await self.connect():
                logger.error("Failed to connect to server")
                return False
            
            self.running = True
            
            # Set up signal handlers for graceful shutdown
            for sig in (signal.SIGINT, signal.SIGTERM):
                asyncio.get_event_loop().add_signal_handler(
                    sig, lambda: asyncio.create_task(self.stop())
                )
            
            logger.info("Client started")
            
            # Start the UI if enabled
            if self.ui_enabled:
                if self.ui_type == 'console':
                    await self.run_console_ui()
                else:
                    logger.warning(f"Unsupported UI type: {self.ui_type}")
                    await self.run_console_ui()
            else:
                # Just keep the client running
                while self.running:
                    await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting client: {e}")
            await self.disconnect()
            return False
    
    async def stop(self):
        """
        Stop the client.
        
        Returns
        -------
        bool
            True if the client was stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping client...")
            
            # Disconnect from the server
            await self.disconnect()
            
            self.running = False
            logger.info("Client stopped")
            
            # Stop the event loop
            asyncio.get_event_loop().stop()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping client: {e}")
            return False
    
    async def run_console_ui(self):
        """
        Run the console UI.
        
        This method provides a simple console interface for the client.
        """
        logger.info("Starting console UI...")
        
        # Print welcome message
        print("\n" + "=" * 50)
        print(f"UnitMCP Example Client: {self.name}")
        print("=" * 50)
        print("Type 'help' for a list of commands, or 'exit' to quit.")
        print("=" * 50 + "\n")
        
        while self.running:
            try:
                # Get user input
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("Command: ")
                )
                
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit']:
                    logger.info("User requested exit")
                    await self.stop()
                    break
                
                # Parse the command
                cmd_parts = command.split()
                cmd_type = cmd_parts[0].lower()
                
                # Process the command
                if cmd_type == 'help':
                    print("\nAvailable commands:")
                    print("  help       - Show this help message")
                    print("  status     - Get server status")
                    print("  exit/quit  - Exit the client\n")
                    
                elif cmd_type == 'status':
                    # Send status command to server
                    response = await self.send_command({'type': 'status'})
                    
                    if response:
                        print("\nServer status:")
                        print(f"  Status: {response.get('status', 'unknown')}")
                        print(f"  Message: {response.get('message', 'No message')}")
                        
                        data = response.get('data', {})
                        if data:
                            print("  Data:")
                            for key, value in data.items():
                                print(f"    {key}: {value}")
                        print()
                    else:
                        print("\nFailed to get server status\n")
                
                else:
                    # Send custom command to server
                    response = await self.send_command({'type': cmd_type})
                    
                    if response:
                        print("\nServer response:")
                        print(f"  Status: {response.get('status', 'unknown')}")
                        print(f"  Message: {response.get('message', 'No message')}")
                        
                        data = response.get('data', {})
                        if data:
                            print("  Data:")
                            for key, value in data.items():
                                print(f"    {key}: {value}")
                        print()
                    else:
                        print("\nFailed to send command to server\n")
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                logger.error(f"Error in console UI: {e}")
                print(f"\nError: {e}\n")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Client")
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/client.yaml",
        help="Path to the client configuration file",
    )
    
    parser.add_argument(
        "--server-host",
        type=str,
        help="Server hostname or IP address (overrides config)",
    )
    
    parser.add_argument(
        "--server-port",
        type=int,
        help="Server port number (overrides config)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser.parse_args()


async def main():
    """
    Main function to run the client.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create the client
    client = ExampleClient(args.config)
    
    # Override configuration with command-line arguments
    if args.server_host:
        client.server_host = args.server_host
    
    if args.server_port:
        client.server_port = args.server_port
    
    try:
        if await client.start():
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
        await client.stop()
        return 0
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        await client.stop()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
