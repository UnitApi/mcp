#!/usr/bin/env python3
"""
LLM Hardware Control Example

This example demonstrates how to use the LLMMCPHardwareServer class to create an MCP server
that allows LLMs to control hardware through natural language.
"""

import asyncio
import logging
import os
import json
import argparse
from typing import Dict, Any, List

from dotenv import load_dotenv
from unitmcp.protocols import get_llm_mcp_hardware_server

# Get the LLMMCPHardwareServer class
LLMMCPHardwareServer = get_llm_mcp_hardware_server()

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Get environment variables
RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="LLM Hardware Control Example")
    parser.add_argument(
        "--host", 
        default=RPI_HOST,
        help=f"Raspberry Pi hostname or IP address (default: {RPI_HOST})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=RPI_PORT,
        help=f"Raspberry Pi port (default: {RPI_PORT})"
    )
    parser.add_argument(
        "--server-name",
        default="Hardware Control",
        help="Name of the MCP server (default: Hardware Control)"
    )
    return parser.parse_args()


async def custom_tool_example(server: LLMMCPHardwareServer):
    """Example of adding a custom tool to the server."""
    
    @server.register_tool
    async def run_sequence(sequence_name: str, duration: int = 5) -> Dict[str, Any]:
        """
        Run a predefined hardware sequence.
        
        Args:
            sequence_name: Name of the sequence to run ('light_show', 'alarm', etc.)
            duration: Duration of the sequence in seconds
            
        Returns:
            A dictionary with the result of the operation
        """
        client = await server.get_hardware_client()
        
        try:
            logger.info(f"Running sequence '{sequence_name}' for {duration} seconds")
            
            if sequence_name.lower() == "light_show":
                # Example: Blink multiple LEDs in sequence
                pins = [17, 18, 27]  # Example GPIO pins
                
                # Set up pins
                for pin in pins:
                    await client.setup_pin(pin, "output")
                
                # Run light show for specified duration
                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) < duration:
                    for pin in pins:
                        await client.write_pin(pin, 1)
                        await asyncio.sleep(0.2)
                        await client.write_pin(pin, 0)
                    
                    await asyncio.sleep(0.5)
                
                return {
                    "success": True,
                    "message": f"Light show sequence completed ({duration} seconds)"
                }
                
            elif sequence_name.lower() == "alarm":
                # Example: Trigger alarm sequence (lights + sound)
                alarm_pin = 17  # Example GPIO pin for alarm light
                
                # Set up pin
                await client.setup_pin(alarm_pin, "output")
                
                # Run alarm sequence
                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) < duration:
                    # Blink alarm light
                    await client.write_pin(alarm_pin, 1)
                    await asyncio.sleep(0.5)
                    await client.write_pin(alarm_pin, 0)
                    await asyncio.sleep(0.5)
                
                return {
                    "success": True,
                    "message": f"Alarm sequence completed ({duration} seconds)"
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Unknown sequence: {sequence_name}"
                }
                
        except Exception as e:
            logger.error(f"Error running sequence: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}


def main():
    """Main function."""
    args = parse_args()
    
    # Create LLM MCP Hardware Server
    server = LLMMCPHardwareServer(
        server_name=args.server_name,
        rpi_host=args.host,
        rpi_port=args.port,
        dependencies=["pydub", "simpleaudio"]
    )
    
    # Register custom tools (this is optional)
    asyncio.run(custom_tool_example(server))
    
    logger.info(f"Starting LLM MCP Hardware Server ({args.server_name})")
    logger.info(f"Connected to Raspberry Pi at {args.host}:{args.port}")
    logger.info("Use Ctrl+C to stop the server")
    
    # Run the server
    server.run()


if __name__ == "__main__":
    main()
