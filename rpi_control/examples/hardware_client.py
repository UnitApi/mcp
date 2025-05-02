#!/usr/bin/env python3
"""
Hardware Control Client

This script sends hardware control commands to the hardware server.
It can be used to control GPIO pins, I2C devices, and get system status.
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import socket
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_system_info():
    """Log system information for debugging purposes."""
    logger.info("=== CLIENT SYSTEM INFORMATION ===")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Get IP addresses
    logger.info("IP addresses:")
    try:
        hostname = socket.gethostname()
        ip_addresses = socket.getaddrinfo(hostname, None)
        for addrinfo in ip_addresses:
            if addrinfo[0] == socket.AF_INET:  # Only IPv4
                logger.info(f"  - {addrinfo[4][0]}")
    except Exception as e:
        logger.error(f"Error getting IP addresses: {e}")
    
    logger.info("=== END SYSTEM INFORMATION ===")

async def send_command(host: str, port: int, command: Dict[str, Any]) -> Dict[str, Any]:
    """Send a command to the hardware server and return the response."""
    try:
        # Connect to the server
        logger.info(f"[CONNECTION] Connecting to server at {host}:{port}")
        reader, writer = await asyncio.open_connection(host, port)
        logger.info(f"[CONNECTION] Successfully connected to {host}:{port}")
        
        # Send the command
        command_json = json.dumps(command)
        logger.info(f"[COMMAND] Sending command: {command_json}")
        writer.write(command_json.encode())
        await writer.drain()
        
        # Read the response
        data = await reader.read(4096)
        response = json.loads(data.decode())
        logger.info(f"[RESPONSE] Received response: {json.dumps(response)}")
        
        # Close the connection
        writer.close()
        await writer.wait_closed()
        
        return response
    except ConnectionRefusedError:
        logger.error(f"[ERROR] Connection refused to {host}:{port}")
        return {"status": "error", "message": f"Connection refused to {host}:{port}"}
    except json.JSONDecodeError:
        logger.error(f"[ERROR] Invalid JSON response: {data.decode() if 'data' in locals() else 'No data'}")
        return {"status": "error", "message": "Invalid JSON response"}
    except Exception as e:
        logger.error(f"[ERROR] Error sending command: {e}")
        return {"status": "error", "message": str(e)}

async def main():
    """Main function to parse arguments and send commands."""
    parser = argparse.ArgumentParser(description='Hardware Control Client')
    parser.add_argument('--host', default='127.0.0.1', help='Host where the server is running')
    parser.add_argument('--port', type=int, default=8082, help='Port where the server is listening')
    parser.add_argument('--command', default='status', help='Command to send (gpio, i2c, status)')
    parser.add_argument('--pin', type=int, help='GPIO pin number (for gpio command)')
    parser.add_argument('--state', help='GPIO pin state (on/off, for gpio command)')
    parser.add_argument('--address', help='I2C device address (for i2c command)')
    parser.add_argument('--register', help='I2C register (for i2c command)')
    parser.add_argument('--value', help='I2C value to write (for i2c command)')
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"[STARTUP] Hardware Control Client starting at {datetime.now().isoformat()}")
    logger.info(f"[CONFIG] Host: {args.host}, Port: {args.port}, Command: {args.command}")
    
    # Log system information
    log_system_info()
    
    # Prepare the command based on arguments
    command = {"action": args.command}
    
    if args.command == "gpio":
        if args.pin is None or args.state is None:
            logger.error("[ERROR] GPIO command requires --pin and --state arguments")
            return 1
        command["pin"] = args.pin
        command["state"] = args.state
    
    elif args.command == "i2c":
        if args.address is None or args.register is None:
            logger.error("[ERROR] I2C command requires --address and --register arguments")
            return 1
        command["address"] = args.address
        command["register"] = args.register
        if args.value is not None:
            command["value"] = args.value
    
    # Add client information to the command
    command["client_hostname"] = socket.gethostname()
    command["timestamp"] = datetime.now().isoformat()
    
    # Send the command
    response = await send_command(args.host, args.port, command)
    
    # Check the response
    if response["status"] == "success":
        logger.info(f"[RESULT] Command executed successfully")
        if "message" in response:
            logger.info(f"[RESULT] {response['message']}")
        if "value" in response:
            logger.info(f"[RESULT] Value: {response['value']}")
        return 0
    else:
        logger.error(f"[RESULT] Command failed: {response.get('message', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        if exit_code == 0:
            logger.info("[RESULT] Operation completed successfully")
        else:
            logger.error("[RESULT] Operation failed")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("[CLIENT] Client stopped by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"[ERROR] Client error: {e}")
        sys.exit(1)
