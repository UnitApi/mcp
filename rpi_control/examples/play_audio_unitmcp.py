#!/usr/bin/env python3
"""
Play audio file on remote device using MCP Hardware Client.
"""

import os
import argparse
from unitmcp import MCPHardwareClient
from dotenv import load_dotenv
import base64
import asyncio

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))
DEFAULT_MP3 = os.getenv('DEFAULT_MP3', 'test.mp3')
DEFAULT_WAV = os.getenv('DEFAULT_WAV', 'test.wav')


async def main():
    parser = argparse.ArgumentParser(description="Play audio file on remote device using MCP Hardware Client")
    parser.add_argument('--file', '-f', type=str, help='Path to .mp3 or .wav file to play (default: env DEFAULT_MP3 or DEFAULT_WAV)')
    args = parser.parse_args()

    # Determine which file to play
    if args.file:
        file_path = args.file
    elif os.path.isfile(DEFAULT_WAV):
        file_path = DEFAULT_WAV
    elif os.path.isfile(DEFAULT_MP3):
        file_path = DEFAULT_MP3
    else:
        print("No audio file specified and no default found. Exiting.")
        return

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.mp3', '.wav']:
        print("Unsupported file type. Please provide a .wav or .mp3 file.")
        return

    print(f"Connecting to MCP server at {RPI_HOST}:{RPI_PORT}")
    client = MCPHardwareClient(RPI_HOST, RPI_PORT)
    await client.connect()

    print(f"Reading and encoding audio file: {file_path}")
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    params = {"audio_data": audio_b64, "format": ext[1:]}
    print(f"Sending playAudio command for {file_path}")
    try:
        result = await client.send_request("audio.playAudio", params)
        if result.get("status") == "audio_played":
            print("Audio playback started successfully.")
        else:
            print(f"Failed to start audio playback: {result}")
    except Exception as e:
        print(f"Error during audio playback: {e}")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
