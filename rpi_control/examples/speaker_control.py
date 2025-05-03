#!/usr/bin/env python3
"""
Speaker Control Example

This script demonstrates how to play audio files (WAV or MP3) either locally or on a remote device.
It can be used with the UnitMCP hardware client for remote playback.
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add the project's src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    import simpleaudio as sa
except ImportError:
    print("simpleaudio not found, trying to install...")
    os.system(f"{sys.executable} -m pip install simpleaudio")
    import simpleaudio as sa

try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
except ImportError:
    print("pydub not found, trying to install...")
    os.system(f"{sys.executable} -m pip install pydub")
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play

# Try to import UnitMCP utilities
try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_audio_dir, get_default_volume, get_simulation_mode
    USE_UNITMCP = True
except ImportError:
    print(f"Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient
        from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_audio_dir, get_default_volume, get_simulation_mode
        print("Successfully imported unitmcp module after path adjustment.")
        USE_UNITMCP = True
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        print("Using local playback only.")
        USE_UNITMCP = False

# Load environment variables
env = EnvLoader()

def play_wav(file_path):
    """Play a WAV file locally using simpleaudio."""
    print(f"Playing WAV file: {file_path}")
    wave_obj = sa.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def play_mp3(file_path):
    """Play an MP3 file locally using pydub."""
    print(f"Playing MP3 file: {file_path}")
    audio = AudioSegment.from_mp3(file_path)
    pydub_play(audio)

async def is_server_active(host, port, timeout=2):
    """Check if the MCP server is active and responding."""
    import asyncio
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def play_remote(file_path, host=None, port=None):
    """Play an audio file on a remote device using the MCP hardware client."""
    import base64
    import asyncio
    
    # Use provided parameters or environment variables
    rpi_host = host or get_rpi_host()
    rpi_port = port or get_rpi_port()
    
    if not await is_server_active(rpi_host, rpi_port):
        print(f"ERROR: No MCP server running at {rpi_host}:{rpi_port}. Start the server and try again.")
        return
    
    client = MCPHardwareClient(rpi_host, rpi_port)
    await client.connect()
    
    ext = os.path.splitext(file_path)[1].lower()[1:]
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    params = {"audio_data": audio_b64, "format": ext}
    print(f"Sending playAudio command for {file_path} to {rpi_host}:{rpi_port}")
    
    try:
        result = await client.send_request("audio.playAudio", params)
        if result.get("status") == "audio_played":
            print("Audio playback started successfully on remote device.")
        else:
            print(f"Failed to start remote audio playback: {result}")
    except Exception as e:
        print(f"Error during remote audio playback: {e}")
    
    await client.disconnect()

def main():
    """Main function to parse arguments and play audio files."""
    parser = argparse.ArgumentParser(description="Speaker control example: play WAV or MP3 file on remote device.")
    parser.add_argument('--file', '-f', help='Path to .wav or .mp3 file to play')
    parser.add_argument('--host', default=None, help='MCP server hostname or IP (overrides env var)')
    parser.add_argument('--port', type=int, default=None, help='MCP server port (overrides env var)')
    parser.add_argument('--remote', action='store_true', help='Play audio on remote device using MCP')
    parser.add_argument('--local', action='store_true', help='Force local playback even if remote is available')
    parser.add_argument('--env-file', default=None, help='Path to .env file')
    args = parser.parse_args()
    
    # Load environment variables from specified file if provided
    if args.env_file:
        env = EnvLoader(args.env_file)
    
    # Determine file path
    file_path = args.file
    if not file_path:
        # Try to use environment variables for default files
        ext = env.get('DEFAULT_AUDIO_FORMAT', 'wav').lower()
        if ext == 'mp3':
            file_path = env.get('DEFAULT_MP3', 'test.mp3')
        else:
            file_path = env.get('DEFAULT_WAV', 'test.wav')
    
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        audio_dir = get_audio_dir()
        if audio_dir:
            alt_path = os.path.join(audio_dir, os.path.basename(file_path))
            if os.path.isfile(alt_path):
                print(f"Found file in audio directory: {alt_path}")
                file_path = alt_path
            else:
                print(f"File not found in audio directory either: {alt_path}")
                sys.exit(1)
        else:
            sys.exit(1)
    
    # Determine if we should use remote playback
    use_remote = args.remote or (USE_UNITMCP and not args.local)
    
    if use_remote and USE_UNITMCP:
        import asyncio
        asyncio.run(play_remote(file_path, args.host, args.port))
        return
    
    # Local playback
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.wav':
        play_wav(file_path)
    elif ext == '.mp3':
        play_mp3(file_path)
    else:
        print("Unsupported file type. Please provide a .wav or .mp3 file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
