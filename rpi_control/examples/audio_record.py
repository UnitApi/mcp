#!/usr/bin/env python3
"""
Audio Recording Example

This example demonstrates how to record audio using the MCP Hardware Client.
"""

import logging
import asyncio
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

async def main():
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
    client = MCPHardwareClient(RPI_HOST, RPI_PORT)
    
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to the MCP server at {RPI_HOST} as {RPI_USERNAME}: {e}")
        return
    try:
        logger.info(f"Starting audio recording for {args.duration} seconds...")
        params = {
            "duration": args.duration,
            "sample_rate": args.sample_rate,
            "channels": args.channels,
        }
        result = await client.send_request("audio.record", params)
        if result.get("success", True):
            logger.info(f"Recording completed successfully")
            logger.info(f"Saving to {args.output}")
            # Save audio data if present
            audio_data = result.get("audio_data")
            if audio_data:
                import base64
                audio_bytes = base64.b64decode(audio_data)
                with open(args.output, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"Audio saved to {args.output}")
            else:
                logger.warning("No audio data returned from server.")
        else:
            logger.error(f"Recording failed: {result.get('message', 'Unknown error')}")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await client.disconnect()
        logger.info("Example completed")

if __name__ == "__main__":
    asyncio.run(main())
