#!/usr/bin/env python3
"""
Test Script for Enhanced Hardware Server Simulation Mode

This script tests the simulation mode of the enhanced hardware server
by sending various commands and verifying that they succeed even when
hardware is not available.
"""

import argparse
import json
import logging
import socket
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def send_command(host, port, command_data):
    """Send a command to the hardware server and return the response."""
    try:
        # Create a socket connection to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # Send the command
            command_json = json.dumps(command_data)
            logger.info(f"Sending command: {command_json}")
            s.sendall(command_json.encode())
            
            # Receive the response
            response_data = s.recv(4096)
            if not response_data:
                raise ConnectionError("No response received from server")
            
            # Parse the response
            response = json.loads(response_data.decode())
            logger.info(f"Received response: {response}")
            
            return response
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return {"status": "error", "message": f"Connection error: {e}"}

def test_status_command(host, port):
    """Test the status command."""
    logger.info("Testing STATUS command...")
    response = send_command(host, port, {"action": "status"})
    
    if response["status"] == "success":
        logger.info("STATUS command successful")
        
        # Check if simulation mode is enabled
        hardware_info = response.get("hardware", {})
        simulation_mode = hardware_info.get("simulation_mode", False)
        logger.info(f"Simulation mode: {'Enabled' if simulation_mode else 'Disabled'}")
        
        # Log hardware availability
        logger.info(f"GPIO Available: {'Yes' if hardware_info.get('gpio_available', False) else 'No'}")
        logger.info(f"I2C Available: {'Yes' if hardware_info.get('i2c_available', False) else 'No'}")
        logger.info(f"LCD Available: {'Yes' if hardware_info.get('lcd_available', False) else 'No'}")
        logger.info(f"Audio Available: {'Yes' if hardware_info.get('audio_available', False) else 'No'}")
        logger.info(f"LED Matrix Available: {'Yes' if hardware_info.get('led_matrix_available', False) else 'No'}")
        
        return True
    else:
        logger.error(f"STATUS command failed: {response.get('message', 'Unknown error')}")
        return False

def test_gpio_command(host, port):
    """Test the GPIO command."""
    logger.info("Testing GPIO command...")
    response = send_command(host, port, {
        "action": "gpio",
        "pin": 18,
        "state": "on"
    })
    
    if response["status"] == "success":
        logger.info("GPIO command successful")
        return True
    else:
        logger.error(f"GPIO command failed: {response.get('message', 'Unknown error')}")
        return False

def test_lcd_command(host, port):
    """Test the LCD command."""
    logger.info("Testing LCD command...")
    response = send_command(host, port, {
        "action": "lcd",
        "text": "Simulation Test",
        "line": 0
    })
    
    if response["status"] == "success":
        logger.info("LCD command successful")
        return True
    else:
        logger.error(f"LCD command failed: {response.get('message', 'Unknown error')}")
        return False

def test_i2c_command(host, port):
    """Test the I2C command."""
    logger.info("Testing I2C command...")
    response = send_command(host, port, {
        "action": "i2c",
        "address": "0x48",
        "register": "0x00"
    })
    
    if response["status"] == "success":
        logger.info("I2C command successful")
        return True
    else:
        logger.error(f"I2C command failed: {response.get('message', 'Unknown error')}")
        return False

def test_speaker_command(host, port):
    """Test the speaker command."""
    logger.info("Testing speaker command...")
    response = send_command(host, port, {
        "action": "speaker",
        "sub_action": "speak",
        "text": "This is a simulation test"
    })
    
    if response["status"] == "success":
        logger.info("Speaker command successful")
        return True
    else:
        logger.error(f"Speaker command failed: {response.get('message', 'Unknown error')}")
        return False

def test_led_matrix_command(host, port):
    """Test the LED matrix command."""
    logger.info("Testing LED matrix command...")
    response = send_command(host, port, {
        "action": "led_matrix",
        "sub_action": "text",
        "data": {
            "text": "TEST",
            "x": 0,
            "y": 0
        }
    })
    
    if response["status"] == "success":
        logger.info("LED matrix command successful")
        return True
    else:
        logger.error(f"LED matrix command failed: {response.get('message', 'Unknown error')}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Enhanced Hardware Server Simulation Mode')
    parser.add_argument('--host', default='localhost', help='Server hostname or IP address')
    parser.add_argument('--port', type=int, default=8082, help='Server port')
    args = parser.parse_args()
    
    logger.info(f"Starting simulation mode test at {datetime.now().isoformat()}")
    logger.info(f"Connecting to server at {args.host}:{args.port}")
    
    # Run all tests
    tests = [
        ("Status", test_status_command),
        ("GPIO", test_gpio_command),
        ("LCD", test_lcd_command),
        ("I2C", test_i2c_command),
        ("Speaker", test_speaker_command),
        ("LED Matrix", test_led_matrix_command)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n=== Running {test_name} Test ===")
        try:
            success = test_func(args.host, args.port)
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} raised an exception: {e}")
            results.append((test_name, False))
        
        # Add a small delay between tests
        time.sleep(0.5)
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    all_passed = True
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("\nAll tests PASSED! Simulation mode is working correctly.")
        return 0
    else:
        logger.error("\nSome tests FAILED. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
