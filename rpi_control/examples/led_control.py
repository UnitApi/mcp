#!/usr/bin/env python3
"""
LED Control Example

This example demonstrates how to control an LED using the MCP Hardware Client.
"""

import logging
import time
import os
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to demonstrate LED control.
    """
    # Create and connect to the MCP hardware client
    client_config = {
        "server": RPI_HOST,
        "port": RPI_PORT,
        "protocol": "http"
    }
    client = MCPHardwareClient(client_config)
    
    # Connect to the server
    if not client.connect():
        logger.error("Failed to connect to the MCP server")
        return
    
    try:
        # Set up the GPIO pin for the LED
        pin = 17
        logger.info(f"Setting up GPIO pin {pin} as output")
        result = client.setup_pin(pin, "output")
        logger.info(f"Setup result: {result}")
        
        # Turn on the LED
        logger.info("Turning on the LED")
        result = client.control_led("led1", "on")
        logger.info(f"Control result: {result}")
        
        # Wait for a moment
        time.sleep(2)
        
        # Blink the LED
        logger.info("Blinking the LED")
        for _ in range(5):
            # Turn on
            client.write_pin(pin, 1)
            time.sleep(0.5)
            
            # Turn off
            client.write_pin(pin, 0)
            time.sleep(0.5)
        
        # Turn off the LED
        logger.info("Turning off the LED")
        result = client.control_led("led1", "off")
        logger.info(f"Control result: {result}")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Disconnect from the server
        client.disconnect()
        logger.info("Example completed")

if __name__ == "__main__":
    main()
