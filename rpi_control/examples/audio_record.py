#!/usr/bin/env python3
"""
Audio Recording Example

This example demonstrates how to record audio using the MCP Hardware Client.
"""

import logging
import time
import argparse
import os
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_USERNAME = os.getenv('RPI_USERNAME', 'pi')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to demonstrate audio recording.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Record audio using MCP Hardware Client")
    parser.add_argument("--duration", type=int, default=5, help="Duration of recording in seconds")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate in Hz")
    parser.add_argument("--channels", type=int, default=1, help="Number of audio channels (1 for mono, 2 for stereo)")
    parser.add_argument("--output", type=str, default="recording.wav", help="Output file name")
    args = parser.parse_args()
    
    # Create and connect to the MCP hardware client
    client_config = {
        "server": RPI_HOST,
        "port": RPI_PORT,
        "protocol": "http"
    }
    client = MCPHardwareClient(client_config)
    
    # Connect to the server
    if not client.connect():
        logger.error(f"Failed to connect to the MCP server at {RPI_HOST} as {RPI_USERNAME}")
        return
    try:
        logger.info(f"Starting audio recording for {args.duration} seconds...")
        result = client.start_audio_record(duration=args.duration, sample_rate=args.sample_rate, channels=args.channels, output=args.output)
        if result.get("success", True):
            logger.info(f"Recording completed successfully")
            logger.info(f"Saving to {args.output}")
            logger.info(f"Audio saved to {args.output}")
        else:
            logger.error(f"Recording failed: {result.get('message', 'Unknown error')}")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        client.disconnect()
        logger.info("Example completed")

if __name__ == "__main__":
    main()
