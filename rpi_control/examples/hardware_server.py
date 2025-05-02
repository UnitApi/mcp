#!/usr/bin/env python3
"""
Hardware Control Server

This script runs a server that listens for hardware control commands
and executes them on the local machine. It's designed to run on a Raspberry Pi
or similar device with GPIO access.
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables
clients = {}  # Store connected clients
hardware_state = {
    "gpio": {},
    "i2c": {},
    "status": "ready",
    "last_command": None,
    "last_command_time": None
}

# Check if running on a Raspberry Pi
def is_raspberry_pi() -> bool:
    """Check if the script is running on a Raspberry Pi."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            return 'raspberry pi' in model.lower()
    except:
        return False
    
# Try to import GPIO library if on Raspberry Pi
GPIO = None
if is_raspberry_pi():
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        logger.info("[HARDWARE] GPIO library initialized successfully")
    except ImportError:
        logger.warning("[HARDWARE] RPi.GPIO library not available")

# Try to import I2C library if available
I2C = None
try:
    import smbus
    I2C = smbus.SMBus(1)  # Use bus 1
    logger.info("[HARDWARE] I2C library initialized successfully")
except ImportError:
    logger.warning("[HARDWARE] smbus library not available")

def log_system_info():
    """Log system information for debugging purposes."""
    logger.info("=== SERVER SYSTEM INFORMATION ===")
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
    
    # Check for GPIO
    if GPIO:
        logger.info("GPIO available: Yes")
    else:
        logger.info("GPIO available: No")
    
    # Check for I2C
    if I2C:
        logger.info("I2C available: Yes")
    else:
        logger.info("I2C available: No")
    
    logger.info("=== END SYSTEM INFORMATION ===")

async def handle_gpio_command(pin: int, state: str) -> Dict[str, Any]:
    """Handle GPIO commands."""
    if not GPIO:
        return {"status": "error", "message": "GPIO not available"}
    
    try:
        # Convert pin to int and state to boolean
        pin = int(pin)
        if state.lower() in ['on', 'high', '1', 'true']:
            value = GPIO.HIGH
            state_str = "HIGH"
        else:
            value = GPIO.LOW
            state_str = "LOW"
        
        # Set up the pin as output if not already
        if pin not in hardware_state["gpio"]:
            GPIO.setup(pin, GPIO.OUT)
            hardware_state["gpio"][pin] = "output"
        
        # Set the pin state
        GPIO.output(pin, value)
        logger.info(f"[HARDWARE] Set GPIO pin {pin} to {state_str}")
        
        return {"status": "success", "message": f"GPIO pin {pin} set to {state_str}"}
    except Exception as e:
        logger.error(f"[HARDWARE] GPIO error: {e}")
        return {"status": "error", "message": f"GPIO error: {e}"}

async def handle_i2c_command(address: int, register: int, value: Optional[int] = None) -> Dict[str, Any]:
    """Handle I2C commands."""
    if not I2C:
        return {"status": "error", "message": "I2C not available"}
    
    try:
        # Convert to integers
        address = int(address, 16) if isinstance(address, str) else int(address)
        register = int(register, 16) if isinstance(register, str) else int(register)
        
        if value is not None:
            # Write to I2C
            value = int(value, 16) if isinstance(value, str) else int(value)
            I2C.write_byte_data(address, register, value)
            logger.info(f"[HARDWARE] Write to I2C device 0x{address:02X}, register 0x{register:02X}, value 0x{value:02X}")
            return {"status": "success", "message": f"Wrote 0x{value:02X} to I2C device 0x{address:02X}, register 0x{register:02X}"}
        else:
            # Read from I2C
            value = I2C.read_byte_data(address, register)
            logger.info(f"[HARDWARE] Read from I2C device 0x{address:02X}, register 0x{register:02X}, value 0x{value:02X}")
            return {"status": "success", "message": f"Read 0x{value:02X} from I2C device 0x{address:02X}, register 0x{register:02X}", "value": value}
    except Exception as e:
        logger.error(f"[HARDWARE] I2C error: {e}")
        return {"status": "error", "message": f"I2C error: {e}"}

async def handle_status_command() -> Dict[str, Any]:
    """Handle status command."""
    status_info = {
        "status": "success",
        "message": "System status",
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "time": datetime.now().isoformat(),
        },
        "hardware": {
            "gpio_available": GPIO is not None,
            "i2c_available": I2C is not None,
            "gpio_pins": hardware_state["gpio"],
            "last_command": hardware_state["last_command"],
            "last_command_time": hardware_state["last_command_time"],
        }
    }
    
    # Add Raspberry Pi specific information if available
    if is_raspberry_pi():
        try:
            # Get CPU temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                status_info["system"]["cpu_temperature"] = f"{temp:.1f}°C"
        except:
            pass
        
        try:
            # Get memory information
            mem_info = subprocess.check_output(['free', '-h']).decode('utf-8')
            status_info["system"]["memory_info"] = mem_info.split('\n')[1].split()[1:4]
        except:
            pass
    
    logger.info(f"[HARDWARE] Status command executed")
    return status_info

async def process_command(command_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a command from a client."""
    action = command_data.get("action", "")
    
    # Update last command information
    hardware_state["last_command"] = action
    hardware_state["last_command_time"] = datetime.now().isoformat()
    
    if action == "gpio":
        pin = command_data.get("pin")
        state = command_data.get("state")
        if pin is None or state is None:
            return {"status": "error", "message": "Missing pin or state parameter"}
        return await handle_gpio_command(pin, state)
    
    elif action == "i2c":
        address = command_data.get("address")
        register = command_data.get("register")
        value = command_data.get("value")
        if address is None or register is None:
            return {"status": "error", "message": "Missing address or register parameter"}
        return await handle_i2c_command(address, register, value)
    
    elif action == "status":
        return await handle_status_command()
    
    elif action == "ping":
        # Simple ping command for server verification
        logger.info(f"[COMMAND] Ping received")
        return {"status": "success", "message": "pong"}
    
    else:
        logger.warning(f"[COMMAND] Unknown action: {action}")
        return {"status": "error", "message": f"Unknown action: {action}"}

async def handle_client(reader, writer):
    """Handle client connection."""
    addr = writer.get_extra_info('peername')
    client_id = f"{addr[0]}:{addr[1]}"
    clients[client_id] = {"reader": reader, "writer": writer, "connected_at": datetime.now().isoformat()}
    
    logger.info(f"[CONNECTION] New client connected from {client_id}")
    
    try:
        # Read data from client
        data = await reader.read(4096)
        if not data:
            logger.info(f"[CONNECTION] Client {client_id} disconnected (no data)")
            del clients[client_id]
            writer.close()
            return
        
        # Parse the command
        try:
            command_data = json.loads(data.decode())
            logger.info(f"[COMMAND] Received command from {client_id}: {command_data}")
            
            # Process the command
            response = await process_command(command_data)
            
            # Send response
            writer.write(json.dumps(response).encode())
            await writer.drain()
            logger.info(f"[RESPONSE] Sent response to {client_id}: {response}")
        except json.JSONDecodeError:
            logger.error(f"[ERROR] Invalid JSON from {client_id}: {data.decode()}")
            writer.write(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
            await writer.drain()
        except Exception as e:
            logger.error(f"[ERROR] Error processing command from {client_id}: {e}")
            writer.write(json.dumps({"status": "error", "message": str(e)}).encode())
            await writer.drain()
    except Exception as e:
        logger.error(f"[ERROR] Error handling client {client_id}: {e}")
    finally:
        # Clean up
        logger.info(f"[CONNECTION] Client {client_id} disconnected")
        if client_id in clients:
            del clients[client_id]
        writer.close()

async def verify_server_is_listening(host, port):
    """Verify that the server is listening on the specified port."""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Try to connect to the server
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            logger.info(f"[SERVER] Successfully verified server is listening on port {port}")
            return True
        except:
            if attempt < max_attempts - 1:
                await asyncio.sleep(0.5)
    
    logger.error(f"[SERVER] Failed to verify server is listening on port {port}")
    return False

async def main():
    """Main function to start the server."""
    parser = argparse.ArgumentParser(description='Hardware Control Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8082, help='Port to use for the server')
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"[STARTUP] Hardware Control Server starting at {datetime.now().isoformat()}")
    logger.info(f"[CONFIG] Host: {args.host}, Port: {args.port}")
    
    # Log system information
    log_system_info()
    
    # Start the server
    server = await asyncio.start_server(handle_client, args.host, args.port)
    
    addr = server.sockets[0].getsockname()
    logger.info(f"[SERVER] Listening on {args.host}:{args.port}")
    
    # Verify that the server is listening
    await verify_server_is_listening('127.0.0.1', args.port)
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[SERVER] Server stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Server error: {e}")
    finally:
        # Clean up GPIO if used
        if GPIO:
            GPIO.cleanup()
            logger.info("[HARDWARE] GPIO cleaned up")
