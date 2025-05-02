#!/usr/bin/env python3
"""
Enhanced Hardware Control Client

This script sends commands to the hardware control server to control
various hardware components on a Raspberry Pi or similar device.

Supported components:
- GPIO pins
- I2C devices
- LCD displays (I2C)
- Speakers (audio playback)
- LED matrices
"""

import argparse
import base64
import json
import logging
import os
import platform
import socket
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union

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

def send_command(host: str, port: int, command_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a command to the hardware control server and return the response."""
    try:
        # Add client information to command data
        command_data["client_hostname"] = socket.gethostname()
        command_data["timestamp"] = datetime.now().isoformat()
        
        # Create a socket connection to the server
        logger.info(f"[CONNECTION] Connecting to server at {host}:{port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            logger.info(f"[CONNECTION] Successfully connected to {host}:{port}")
            
            # Send the command
            command_json = json.dumps(command_data)
            logger.info(f"[COMMAND] Sending command: {command_json}")
            s.sendall(command_json.encode())
            
            # Receive the response
            response_data = s.recv(4096)
            if not response_data:
                raise ConnectionError("No response received from server")
            
            # Parse the response
            response = json.loads(response_data.decode())
            logger.info(f"[RESPONSE] Received response: {response}")
            
            return response
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Invalid JSON response: {e}")
        return {"status": "error", "message": f"Invalid JSON response: {e}"}
    except ConnectionRefusedError:
        logger.error(f"[ERROR] Connection refused by {host}:{port}")
        return {"status": "error", "message": f"Connection refused by {host}:{port}"}
    except socket.timeout:
        logger.error(f"[ERROR] Connection to {host}:{port} timed out")
        return {"status": "error", "message": f"Connection to {host}:{port} timed out"}
    except Exception as e:
        logger.error(f"[ERROR] Connection error: {e}")
        return {"status": "error", "message": f"Connection error: {e}"}

def handle_status_command(host: str, port: int) -> int:
    """Handle the status command."""
    response = send_command(host, port, {"action": "status"})
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info("[RESULT] System status")
        
        # Print system information
        system_info = response.get("system", {})
        if system_info:
            print("\nSystem Information:")
            print(f"  Hostname: {system_info.get('hostname', 'N/A')}")
            print(f"  Platform: {system_info.get('platform', 'N/A')}")
            print(f"  Python: {system_info.get('python_version', 'N/A')}")
            print(f"  Time: {system_info.get('time', 'N/A')}")
            
            if "cpu_temperature" in system_info:
                print(f"  CPU Temperature: {system_info['cpu_temperature']}")
            
            if "memory_info" in system_info:
                print(f"  Memory (total/used/free): {'/'.join(system_info['memory_info'])}")
        
        # Print hardware information
        hardware_info = response.get("hardware", {})
        if hardware_info:
            print("\nHardware Information:")
            print(f"  GPIO Available: {'Yes' if hardware_info.get('gpio_available', False) else 'No'}")
            print(f"  I2C Available: {'Yes' if hardware_info.get('i2c_available', False) else 'No'}")
            print(f"  Audio Available: {'Yes' if hardware_info.get('audio_available', False) else 'No'}")
            print(f"  LCD Available: {'Yes' if hardware_info.get('lcd_available', False) else 'No'}")
            print(f"  LED Matrix Available: {'Yes' if hardware_info.get('led_matrix_available', False) else 'No'}")
            print(f"  Simulation Mode: {'Yes' if hardware_info.get('simulation_mode', False) else 'No'}")
            
            # Print GPIO pin states
            gpio_pins = hardware_info.get("gpio_pins", {})
            if gpio_pins:
                print("\n  GPIO Pin States:")
                for pin, state in gpio_pins.items():
                    print(f"    Pin {pin}: {state}")
            
            # Print last command information
            last_command = hardware_info.get("last_command")
            last_command_time = hardware_info.get("last_command_time")
            if last_command:
                print(f"\n  Last Command: {last_command}")
                print(f"  Last Command Time: {last_command_time}")
        
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def handle_gpio_command(host: str, port: int, pin: int, state: str) -> int:
    """Handle the GPIO command."""
    response = send_command(host, port, {
        "action": "gpio",
        "pin": pin,
        "state": state
    })
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info(f"[RESULT] {response.get('message', 'GPIO operation completed')}")
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def handle_i2c_command(host: str, port: int, address: str, register: str, value: Optional[str] = None) -> int:
    """Handle the I2C command."""
    command_data = {
        "action": "i2c",
        "address": address,
        "register": register
    }
    
    if value is not None:
        command_data["value"] = value
    
    response = send_command(host, port, command_data)
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info(f"[RESULT] {response.get('message', 'I2C operation completed')}")
        
        # If this was a read operation, print the value
        if "value" in response:
            print(f"\nRead Value: 0x{response['value']:02X} ({response['value']})")
        
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def handle_lcd_command(host: str, port: int, text: Optional[str] = None, line: int = 0, clear: bool = False) -> int:
    """Handle the LCD command."""
    command_data = {
        "action": "lcd",
        "line": line
    }
    
    if clear:
        command_data["clear"] = True
    else:
        command_data["text"] = text
    
    response = send_command(host, port, command_data)
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info(f"[RESULT] {response.get('message', 'LCD operation completed')}")
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def handle_speaker_command(host: str, port: int, sub_action: str, audio_file: Optional[str] = None, text: Optional[str] = None) -> int:
    """Handle the speaker command."""
    command_data = {
        "action": "speaker",
        "sub_action": sub_action
    }
    
    if sub_action == "play_file" and audio_file:
        try:
            # Read the audio file and encode it as base64
            with open(audio_file, "rb") as f:
                file_data = base64.b64encode(f.read()).decode()
            command_data["file_data"] = file_data
        except Exception as e:
            logger.error(f"[ERROR] Failed to read audio file: {e}")
            return 1
    
    elif sub_action == "speak" and text:
        command_data["text"] = text
    
    response = send_command(host, port, command_data)
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info(f"[RESULT] {response.get('message', 'Speaker operation completed')}")
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def handle_led_matrix_command(host: str, port: int, led_action: str, text: Optional[str] = None, x: Optional[int] = None, y: Optional[int] = None) -> int:
    """Handle the LED matrix command."""
    command_data = {
        "action": "led_matrix",
        "sub_action": led_action,
        "data": {}
    }
    
    if led_action == "text":
        if text is None:
            logger.error("[ERROR] Text is required for text LED action")
            return 1
        command_data["data"]["text"] = text
        if x is not None:
            command_data["data"]["x"] = x
        if y is not None:
            command_data["data"]["y"] = y
    
    elif led_action == "pixel":
        if x is None or y is None:
            logger.error("[ERROR] X and Y coordinates are required for pixel LED action")
            return 1
        command_data["data"]["x"] = x
        command_data["data"]["y"] = y
    
    response = send_command(host, port, command_data)
    
    if response["status"] == "success":
        logger.info("[RESULT] Command executed successfully")
        logger.info(f"[RESULT] {response.get('message', 'LED matrix operation completed')}")
        logger.info("[RESULT] Operation completed successfully")
        return 0
    else:
        logger.error(f"[ERROR] Command failed: {response.get('message', 'Unknown error')}")
        return 1

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hardware Control Client')
    parser.add_argument('--host', default='localhost', help='Server hostname or IP address')
    parser.add_argument('--port', type=int, default=8082, help='Server port')
    parser.add_argument('--command', default='status', choices=['status', 'gpio', 'i2c', 'lcd', 'speaker', 'led_matrix'], help='Command to execute')
    
    # GPIO command arguments
    parser.add_argument('--pin', type=int, help='GPIO pin number (for gpio command)')
    parser.add_argument('--state', choices=['on', 'off'], help='GPIO pin state (for gpio command)')
    
    # I2C command arguments
    parser.add_argument('--address', help='I2C device address (for i2c command)')
    parser.add_argument('--register', help='I2C register (for i2c command)')
    parser.add_argument('--value', help='I2C value to write (for i2c command)')
    
    # LCD command arguments
    parser.add_argument('--text', help='Text to display on LCD or speak')
    parser.add_argument('--line', type=int, default=0, help='LCD line number (0 or 1, default: 0)')
    parser.add_argument('--clear', action='store_true', help='Clear the LCD display')
    
    # Speaker command arguments
    parser.add_argument('--sub-action', choices=['play_file', 'play_tone', 'speak'], help='Speaker sub-action')
    parser.add_argument('--audio-file', help='Audio file to play (for play_file sub-action)')
    
    # LED matrix command arguments
    parser.add_argument('--led-action', choices=['clear', 'text', 'pixel'], help='LED matrix action')
    parser.add_argument('--x', type=int, help='X coordinate for LED matrix')
    parser.add_argument('--y', type=int, help='Y coordinate for LED matrix')
    
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"[STARTUP] Hardware Control Client starting at {datetime.now().isoformat()}")
    logger.info(f"[CONFIG] Host: {args.host}, Port: {args.port}, Command: {args.command}")
    
    # Log system information
    log_system_info()
    
    # Execute the command
    try:
        if args.command == 'status':
            return handle_status_command(args.host, args.port)
        
        elif args.command == 'gpio':
            if args.pin is None or args.state is None:
                logger.error("[ERROR] Pin and state are required for GPIO command")
                return 1
            return handle_gpio_command(args.host, args.port, args.pin, args.state)
        
        elif args.command == 'i2c':
            if args.address is None or args.register is None:
                logger.error("[ERROR] Address and register are required for I2C command")
                return 1
            return handle_i2c_command(args.host, args.port, args.address, args.register, args.value)
        
        elif args.command == 'lcd':
            if not args.clear and args.text is None:
                logger.error("[ERROR] Either text or clear flag is required for LCD command")
                return 1
            return handle_lcd_command(args.host, args.port, args.text, args.line, args.clear)
        
        elif args.command == 'speaker':
            if args.sub_action is None:
                logger.error("[ERROR] Sub-action is required for speaker command")
                return 1
            
            if args.sub_action == 'play_file' and args.audio_file is None:
                logger.error("[ERROR] Audio file is required for play_file sub-action")
                return 1
            
            if args.sub_action == 'speak' and args.text is None:
                logger.error("[ERROR] Text is required for speak sub-action")
                return 1
            
            return handle_speaker_command(args.host, args.port, args.sub_action, args.audio_file, args.text)
        
        elif args.command == 'led_matrix':
            if args.led_action is None:
                logger.error("[ERROR] LED action is required for LED matrix command")
                return 1
            
            return handle_led_matrix_command(args.host, args.port, args.led_action, args.text, args.x, args.y)
        
        else:
            logger.error(f"[ERROR] Unknown command: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        logger.info("[INFO] Operation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
