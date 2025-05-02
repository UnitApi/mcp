#!/usr/bin/env python3
"""
Full Demo Example

This script demonstrates a complete workflow for controlling hardware on a Raspberry Pi using the MCP Hardware Client.
"""

import logging
import asyncio
import os
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_USERNAME = os.getenv('RPI_USERNAME', 'pi')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("full_demo")

    logger.info(f"Connecting to MCP server at {RPI_HOST} as {RPI_USERNAME}")
    client = MCPHardwareClient(RPI_HOST, RPI_PORT)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP server at {RPI_HOST} as {RPI_USERNAME}: {e}")
        return

    # LED demo
    pin = 17
    logger.info(f"Setting up GPIO pin {pin} as output for LED.")
    await client.setup_pin(pin, "output")
    logger.info("Turning LED ON.")
    await client.write_pin(pin, 1)
    await asyncio.sleep(2)
    logger.info("Turning LED OFF.")
    await client.write_pin(pin, 0)

    # Audio record demo
    logger.info("Starting audio recording for 3 seconds.")
    params = {"duration": 3, "sample_rate": 44100, "channels": 1}
    result = await client.send_request("audio.record", params)
    if result.get("success", True):
        logger.info("Audio recording complete.")
        audio_data = result.get("audio_data")
        if audio_data:
            import base64
            audio_bytes = base64.b64decode(audio_data)
            with open("demo_recording.wav", "wb") as f:
                f.write(audio_bytes)
            logger.info("Audio saved to demo_recording.wav")
        else:
            logger.warning("No audio data returned from server.")
    else:
        logger.error(f"Recording failed: {result.get('message', 'Unknown error')}")

    logger.info("Demo finished.")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
