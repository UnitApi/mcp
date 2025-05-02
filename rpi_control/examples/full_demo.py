#!/usr/bin/env python3
"""
Full Demo Example

This script demonstrates a complete workflow for controlling hardware on a Raspberry Pi using the MCP Hardware Client.
"""

import logging
import time
import os
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_USERNAME = os.getenv('RPI_USERNAME', 'pi')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("full_demo")

    logger.info(f"Connecting to MCP server at {RPI_HOST} as {RPI_USERNAME}")
    # Connect to MCP Hardware Client
    client = MCPHardwareClient({
        "server": RPI_HOST,
        "port": RPI_PORT,
        "protocol": "http"
    })
    if not client.connect():
        logger.error(f"Failed to connect to MCP server at {RPI_HOST} as {RPI_USERNAME}")
        return

    # LED demo
    pin = 17
    logger.info(f"Setting up GPIO pin {pin} as output for LED.")
    client.setup_pin(pin, "output")
    logger.info("Turning LED ON.")
    client.write_pin(pin, 1)
    time.sleep(2)
    logger.info("Turning LED OFF.")
    client.write_pin(pin, 0)

    # Audio record demo
    logger.info("Starting audio recording for 3 seconds.")
    client.start_audio_record(duration=3, sample_rate=44100, channels=1, output="demo_recording.wav")
    logger.info("Audio recording complete.")

    logger.info("Demo finished.")

if __name__ == "__main__":
    main()
