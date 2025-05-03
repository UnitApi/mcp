#!/usr/bin/env python3
"""
UnitMCP Example Template - Server

This module implements a template server for UnitMCP examples.
It provides a basic server implementation that can be extended
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


class ExampleServer:
    """
    Template server implementation for UnitMCP examples.
    
    This class provides a basic server that:
    - Loads configuration from a YAML file
    - Sets up a TCP server for client connections
    - Handles client requests
    - Processes commands
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the server with the given configuration.
        
        Parameters
        ----------
        config_path : str
            Path to the server configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        self.server = None
        self.clients = set()
        
        # Extract server settings from config
        server_config = self.config.get('server', {})
        self.host = server_config.get('host', 'localhost')
        self.port = server_config.get('port', 8000)
        self.max_connections = server_config.get('max_connections', 10)
        self.timeout = server_config.get('timeout', 30)
        
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
    
    async def start(self):
        """
        Start the server.
        
        Returns
        -------
        bool
            True if the server was started successfully, False otherwise
        """
        try:
            logger.info(f"Starting server on {self.host}:{self.port}")
            
            # Create the server
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port,
                limit=1024 * 1024,  # 1MB limit
            )
            
            self.running = True
            
            # Set up signal handlers for graceful shutdown
            for sig in (signal.SIGINT, signal.SIGTERM):
                asyncio.get_event_loop().add_signal_handler(
                    sig, lambda: asyncio.create_task(self.stop())
                )
            
            logger.info(f"Server started on {self.host}:{self.port}")
            
            # Start serving
            async with self.server:
                await self.server.serve_forever()
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    async def stop(self):
        """
        Stop the server.
        
        Returns
        -------
        bool
            True if the server was stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping server...")
            
            # Close all client connections
            for client in self.clients:
                client.close()
            
            # Close the server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            self.running = False
            logger.info("Server stopped")
            
            # Stop the event loop
            asyncio.get_event_loop().stop()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            return False
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle a client connection.
        
        Parameters
        ----------
        reader : asyncio.StreamReader
            Stream reader for the client connection
        writer : asyncio.StreamWriter
            Stream writer for the client connection
        """
        # Get client address
        addr = writer.get_extra_info('peername')
        logger.info(f"New client connected: {addr}")
        
        # Add client to set
        self.clients.add(writer)
        
        try:
            while self.running:
                # Read data from client
                data = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self.timeout
                )
                
                if not data:
                    break
                
                # Process the command
                try:
                    command = json.loads(data.decode())
                    logger.info(f"Received command from {addr}: {command}")
                    
                    # Process the command
                    response = await self.process_command(command)
                    
                    # Send response to client
                    writer.write(json.dumps(response).encode() + b'\n')
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {addr}: {data.decode()}")
                    writer.write(json.dumps({
                        'status': 'error',
                        'message': 'Invalid JSON'
                    }).encode() + b'\n')
                    await writer.drain()
                    
        except asyncio.TimeoutError:
            logger.warning(f"Client {addr} timed out")
            
        except ConnectionResetError:
            logger.warning(f"Connection reset by client {addr}")
            
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            
        finally:
            # Close the connection
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            # Remove client from set
            self.clients.remove(writer)
            logger.info(f"Client disconnected: {addr}")
    
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a command from a client.
        
        Parameters
        ----------
        command : Dict[str, Any]
            Command from the client
            
        Returns
        -------
        Dict[str, Any]
            Response to the client
        """
        # Get command type
        cmd_type = command.get('type', '')
        
        # Check if command is allowed
        allowed_commands = self.config.get('commands', {}).get('allowed', [])
        if allowed_commands and cmd_type not in allowed_commands:
            return {
                'status': 'error',
                'message': f'Command not allowed: {cmd_type}'
            }
        
        # Process command based on type
        if cmd_type == 'status':
            return {
                'status': 'ok',
                'message': 'Server is running',
                'data': {
                    'clients': len(self.clients),
                    'uptime': 0  # Implement uptime tracking if needed
                }
            }
            
        elif cmd_type == 'help':
            return {
                'status': 'ok',
                'message': 'Available commands',
                'data': {
                    'commands': allowed_commands
                }
            }
            
        else:
            # Use the default command if specified
            default_cmd = self.config.get('commands', {}).get('default', '')
            if default_cmd and default_cmd != cmd_type:
                logger.info(f"Using default command: {default_cmd}")
                command['type'] = default_cmd
                return await self.process_command(command)
            
            return {
                'status': 'error',
                'message': f'Unknown command: {cmd_type}'
            }


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Server")
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/server.yaml",
        help="Path to the server configuration file",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser.parse_args()


async def main():
    """
    Main function to run the server.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start the server
    server = ExampleServer(args.config)
    
    try:
        if await server.start():
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        await server.stop()
        return 0
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        await server.stop()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
