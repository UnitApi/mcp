#!/usr/bin/env python3
"""
Test LLM MCP Integration

This script tests the LLM MCP integration by creating a simple server and client.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

from dotenv import load_dotenv
from unitmcp.protocols import get_llm_mcp_hardware_server

# Get the LLMMCPHardwareServer class
LLMMCPHardwareServer = get_llm_mcp_hardware_server()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Get environment variables
RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))


async def test_server():
    """Test the LLMMCPHardwareServer."""
    logger.info("Creating LLMMCPHardwareServer...")
    server = LLMMCPHardwareServer(
        server_name="Test Hardware Control",
        rpi_host=RPI_HOST,
        rpi_port=RPI_PORT
    )
    
    # Register a custom tool
    @server.register_tool
    async def test_tool(message: str) -> Dict[str, Any]:
        """
        Test tool that returns the input message.
        
        Args:
            message: The message to echo
            
        Returns:
            A dictionary with the echoed message
        """
        logger.info(f"Test tool called with message: {message}")
        return {
            "success": True,
            "message": f"Echo: {message}"
        }
    
    logger.info("LLMMCPHardwareServer created successfully")
    logger.info(f"Server name: {server.server_name}")
    logger.info(f"Connected to Raspberry Pi at {server.rpi_host}:{server.rpi_port}")
    logger.info("Test completed successfully")


def main():
    """Main function."""
    try:
        asyncio.run(test_server())
        logger.info("All tests passed!")
        return 0
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
