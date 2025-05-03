#!/usr/bin/env python3
"""
Raspberry Pi MCP Server Starter Example

This example demonstrates how to use the RPiServerStarter to start the MCP server
on a Raspberry Pi and then connect to it from the MCP Orchestrator.

Usage:
  python rpi_server_starter.py --host 192.168.188.154 --port 8080 --ssh-username pi
"""

import os
import sys
import time
import asyncio
import logging
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unitmcp.runner.rpi_server_starter import RPiServerStarter
from unitmcp.client.client import MCPHardwareClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("RPiServerStarterExample")

async def main():
    """
    Main entry point for the example.
    """
    parser = argparse.ArgumentParser(description="Start the MCP server on a Raspberry Pi and connect to it")
    parser.add_argument("--host", default="192.168.188.154", help="The IP address of the Raspberry Pi")
    parser.add_argument("--port", type=int, default=8080, help="The port to run the MCP server on")
    parser.add_argument("--ssh-username", default="pi", help="SSH username for the Raspberry Pi")
    parser.add_argument("--ssh-password", help="SSH password (optional)")
    parser.add_argument("--ssh-key-path", help="Path to the SSH private key file (optional)")
    parser.add_argument("--server-path", default="~/UnitApi/mcp", help="Path to the MCP server on the Raspberry Pi")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-connect", action="store_true", help="Don't try to connect to the server after starting it")
    
    args = parser.parse_args()
    
    # Create the config dictionary
    config = {
        "host": args.host,
        "port": args.port,
        "ssh_username": args.ssh_username,
        "ssh_password": args.ssh_password,
        "ssh_key_path": args.ssh_key_path,
        "server_path": args.server_path,
        "simulation": args.simulation,
        "verbose": args.verbose
    }
    
    logger.info("Starting RPi Server Starter Example")
    logger.info(f"Host: {args.host}, Port: {args.port}")
    
    # Create the RPi Server Starter
    starter = RPiServerStarter(config)
    
    # Initialize
    logger.info("Initializing RPi Server Starter...")
    if not await starter.initialize():
        logger.error("Failed to initialize RPi Server Starter")
        sys.exit(1)
    
    # Start the server
    logger.info("Starting MCP server...")
    if not await starter.start_server():
        logger.error("Failed to start MCP server")
        sys.exit(1)
    
    logger.info(f"MCP server started successfully on {args.host}:{args.port}")
    
    # Try to connect to the server
    if not args.no_connect:
        logger.info(f"Connecting to MCP server at {args.host}:{args.port}...")
        
        # Create the client
        client = MCPHardwareClient(args.host, args.port)
        
        # Try to connect
        try:
            await client.connect_with_retry(max_retries=5, retry_delay=2.0)
            logger.info("Successfully connected to MCP server")
            
            # Test the connection by getting the server info
            info = await client.get_server_info()
            logger.info(f"Server info: {info}")
            
            # Disconnect
            await client.disconnect()
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
    
    logger.info("Server is now running. Press Ctrl+C to stop the server and exit.")
    
    # Keep the script running to maintain the SSH connection
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping MCP server...")
        await starter.stop_server()
        logger.info("MCP server stopped")

if __name__ == "__main__":
    asyncio.run(main())
