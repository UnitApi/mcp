#!/usr/bin/env python3
"""
Audio Playback Example for UnitMCP

This example demonstrates how to:
1. Connect to the audio subsystem
2. Play a simple sound file
3. Implement text-to-speech functionality
4. Demonstrate volume control

This example uses the UnitMCP hardware client to control audio playback.
"""

import asyncio
import argparse
import platform
import os
import base64
import tempfile
import sys
from typing import Optional

# Add the project's src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    from unitmcp import MCPHardwareClient
    from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_audio_dir, get_default_volume, get_simulation_mode
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
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        print("Please ensure the UnitMCP project is properly installed.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Check if we're on a Raspberry Pi
IS_RPI = platform.machine() in ["armv7l", "aarch64"]


class AudioExample:
    """Audio playback example class."""

    def __init__(self, host: str = None, port: int = None, 
                 audio_dir: str = None, default_volume: int = None):
        """Initialize the audio example.
        
        Args:
            host: The hostname or IP address of the MCP server (overrides env var)
            port: The port of the MCP server (overrides env var)
            audio_dir: Directory containing audio files (overrides env var)
            default_volume: Default volume level (0-100) (overrides env var)
        """
        # Use parameters or environment variables with defaults
        self.host = host or get_rpi_host()
        self.port = port or get_rpi_port()
        self.audio_dir = audio_dir or get_audio_dir()
        self.default_volume = default_volume or get_default_volume()
        self.client: Optional[MCPHardwareClient] = None
        self.temp_files = []
        
    async def connect(self):
        """Connect to the MCP server."""
        print(f"Connecting to MCP server at {self.host}:{self.port}...")
        self.client = MCPHardwareClient(self.host, self.port)
        await self.client.connect()
        print("Connected to MCP server")
        
    async def list_audio_devices(self):
        """List available audio devices."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Listing audio devices...")
        result = await self.client.send_request("audio.listDevices")
        
        if result.get("status") == "success":
            devices = result.get("devices", [])
            print(f"Found {len(devices)} audio devices:")
            
            input_devices = [d for d in devices if d["type"] == "input"]
            output_devices = [d for d in devices if d["type"] == "output"]
            
            print("\nInput devices:")
            for device in input_devices:
                default_marker = " (default)" if device.get("default") else ""
                print(f"  ID: {device['id']}, Name: {device['name']}{default_marker}")
                
            print("\nOutput devices:")
            for device in output_devices:
                default_marker = " (default)" if device.get("default") else ""
                print(f"  ID: {device['id']}, Name: {device['name']}{default_marker}")
        else:
            print("Failed to list audio devices")
            
        return result
        
    async def get_volume(self):
        """Get the current system volume."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Getting current volume...")
        result = await self.client.send_request("audio.getVolume")
        
        if result.get("status") == "success":
            volume = result.get("volume", 0)
            print(f"Current volume: {volume}%")
        else:
            print("Failed to get volume")
            
        return result
        
    async def set_volume(self, volume: int):
        """Set the system volume.
        
        Args:
            volume: Volume level (0-100)
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Setting volume to {volume}%...")
        result = await self.client.send_request("audio.setVolume", {"volume": volume})
        
        if result.get("status") == "volume_set":
            print(f"Volume set to {volume}%")
        else:
            print("Failed to set volume")
            
        return result
        
    async def play_sound_file(self, file_path: str):
        """Play a sound file.
        
        Args:
            file_path: Path to the sound file
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Sound file not found: {file_path}")
            
        print(f"Playing sound file: {file_path}")
        
        # Read the file and encode it as base64
        with open(file_path, "rb") as f:
            audio_data = f.read()
            
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        # Determine format from file extension
        file_format = os.path.splitext(file_path)[1].lower()[1:]
        if file_format == "wav":
            format_type = "wav"
        else:
            format_type = "raw"  # Default to raw format
            
        result = await self.client.send_request("audio.playAudio", {
            "audio_data": audio_base64,
            "format": format_type
        })
        
        if result.get("status") == "audio_played":
            duration = result.get("duration", 0)
            print(f"Audio playback completed. Duration: {duration:.2f} seconds")
        else:
            print("Failed to play audio")
            
        return result
        
    async def text_to_speech(self, text: str, rate: int = 150, volume: float = 1.0):
        """Convert text to speech and play it.
        
        Args:
            text: The text to convert to speech
            rate: Speech rate (words per minute)
            volume: Speech volume (0.0-1.0)
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Converting text to speech: '{text}'")
        result = await self.client.send_request("audio.textToSpeech", {
            "text": text,
            "rate": rate,
            "volume": volume
        })
        
        if result.get("status") == "speech_generated":
            print("Text-to-speech playback completed")
        else:
            print("Failed to generate speech")
            
        return result
        
    async def generate_tone(self, frequency: int = 440, duration: float = 1.0):
        """Generate and play a tone.
        
        Args:
            frequency: Tone frequency in Hz
            duration: Tone duration in seconds
        """
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print(f"Generating tone: {frequency} Hz for {duration} seconds")
        
        # Create a temporary WAV file with the tone
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.temp_files.append(temp_file.name)
        temp_file.close()
        
        # Generate the tone using the MCP server
        result = await self.client.send_request("audio.generateTone", {
            "frequency": frequency,
            "duration": duration,
            "output_file": temp_file.name
        })
        
        if result.get("status") == "tone_generated":
            print(f"Tone generated and saved to {temp_file.name}")
            # Play the generated tone
            await self.play_sound_file(temp_file.name)
        else:
            print("Failed to generate tone")
            
        return result
        
    async def volume_demo(self):
        """Demonstrate volume control."""
        if not self.client:
            raise RuntimeError("Not connected to MCP server")
            
        print("Starting volume control demo...")
        
        # Get current volume
        original_volume_result = await self.get_volume()
        original_volume = original_volume_result.get("volume", 50)
        
        # Set to low volume
        await self.set_volume(20)
        await self.text_to_speech("This is low volume.")
        await asyncio.sleep(1)
        
        # Set to medium volume
        await self.set_volume(50)
        await self.text_to_speech("This is medium volume.")
        await asyncio.sleep(1)
        
        # Set to high volume
        await self.set_volume(80)
        await self.text_to_speech("This is high volume.")
        await asyncio.sleep(1)
        
        # Restore original volume
        await self.set_volume(original_volume)
        print("Volume demo completed")
        
    async def cleanup(self):
        """Clean up resources."""
        # Remove temporary files
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error removing temporary file {file_path}: {e}")
                
        if self.client:
            await self.client.disconnect()
            print("Disconnected from MCP server")
            
    async def run_demo(self, sound_file: str = None, tts_text: str = None):
        """Run the complete audio demo."""
        try:
            await self.connect()
            
            # List audio devices
            await self.list_audio_devices()
            
            # Get current volume
            await self.get_volume()
            
            if sound_file:
                # Play the specified sound file
                await self.play_sound_file(sound_file)
            elif tts_text:
                # Do text-to-speech
                await self.text_to_speech(tts_text)
            else:
                # Text-to-speech demo
                await self.text_to_speech("Welcome to the UnitMCP audio example. This demonstrates text to speech functionality.")
                await asyncio.sleep(1)
                
                # Generate tones
                await self.generate_tone(440, 0.5)  # A4
                await asyncio.sleep(0.1)
                await self.generate_tone(523, 0.5)  # C5
                await asyncio.sleep(0.1)
                await self.generate_tone(659, 0.5)  # E5
                await asyncio.sleep(0.1)
                await self.generate_tone(784, 1.0)  # G5
                
                # Volume control demo
                await self.volume_demo()
                
                # Final message
                await self.text_to_speech("Audio example completed. Thank you for listening!")
            
        finally:
            await self.cleanup()


async def main():
    """Main function to run the audio example."""
    parser = argparse.ArgumentParser(description="UnitMCP Audio Playback Example")
    parser.add_argument("--host", default=None, help="MCP server hostname or IP (overrides env var)")
    parser.add_argument("--port", type=int, default=None, help="MCP server port (overrides env var)")
    parser.add_argument("--sound-file", help="Path to a sound file to play")
    parser.add_argument("--tts", help="Text to convert to speech")
    parser.add_argument("--audio-dir", default=None, help="Directory containing audio files (overrides env var)")
    parser.add_argument("--volume", type=int, default=None, help="Default volume level (0-100) (overrides env var)")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    args = parser.parse_args()
    
    # Load environment variables from specified file if provided
    if args.env_file:
        env = EnvLoader(args.env_file)
    
    if not IS_RPI and get_simulation_mode():
        print("Not running on a Raspberry Pi. Using simulation mode.")
    
    example = AudioExample(
        host=args.host, 
        port=args.port,
        audio_dir=args.audio_dir,
        default_volume=args.volume
    )
    
    try:
        await example.run_demo(sound_file=args.sound_file, tts_text=args.tts)
    finally:
        await example.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting audio example...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
