#!/usr/bin/env python3
"""
Voice Assistant Client

This script implements the client-side of the voice assistant example.
It handles audio recording, playback, and user interface.
"""

import asyncio
import base64
import json
import logging
import os
import sys
import threading
import time
import wave
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import audio libraries
try:
    import pyaudio
    import numpy as np
    from scipy.io import wavfile
except ImportError:
    print("Error: Required audio libraries not found.")
    print("Please install them with: pip install pyaudio numpy scipy")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VoiceAssistantClient:
    """
    Client for the voice assistant example.
    
    This class handles:
    - Audio recording and playback
    - Wake word detection
    - Communication with the server
    - User interface
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the voice assistant client.
        
        Parameters
        ----------
        config_path : str
            Path to the client configuration file
        """
        self.config = self._load_config(config_path)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.reader = None
        self.writer = None
        self.recording = False
        self.listening_for_wake_word = False
        self.processing = False
        self.running = False
        
        # Load audio settings
        self.sample_rate = self.config['audio']['input']['sample_rate']
        self.channels = self.config['audio']['input']['channels']
        self.chunk_size = self.config['audio']['input']['chunk_size']
        self.silence_threshold = self.config['audio']['input']['silence_threshold']
        self.silence_duration = self.config['audio']['input']['silence_duration']
        
        # Load wake word settings
        self.wake_word = self.config['ui']['wake_word'].lower()
        self.wake_word_sensitivity = self.config['ui']['wake_word_sensitivity']
        
        # Load connection settings
        self.server_host = self.config['connection']['server_host']
        self.server_port = self.config['connection']['server_port']
        self.timeout = self.config['connection']['timeout']
        self.reconnect_attempts = self.config['connection']['reconnect_attempts']
        self.reconnect_delay = self.config['connection']['reconnect_delay']
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the client configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
            
        Returns
        -------
        Dict[str, Any]
            Client configuration
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    async def connect(self) -> bool:
        """
        Connect to the voice assistant server.
        
        Returns
        -------
        bool
            True if connection was successful, False otherwise
        """
        for attempt in range(self.reconnect_attempts):
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.server_host,
                    self.server_port,
                )
                logger.info(f"Connected to server at {self.server_host}:{self.server_port}")
                return True
            
            except (ConnectionRefusedError, OSError) as e:
                logger.error(f"Connection attempt {attempt + 1}/{self.reconnect_attempts} failed: {e}")
                
                if attempt < self.reconnect_attempts - 1:
                    logger.info(f"Retrying in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    logger.error("Failed to connect to server after multiple attempts")
                    return False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to the server and receive a response.
        
        Parameters
        ----------
        message : Dict[str, Any]
            Message to send to the server
            
        Returns
        -------
        Dict[str, Any]
            Response from the server
        """
        if not self.reader or not self.writer:
            logger.error("Not connected to server")
            return {'type': 'error', 'message': 'Not connected to server'}
        
        try:
            # Encode the message
            message_bytes = json.dumps(message).encode('utf-8')
            
            # Send the message length
            self.writer.write(len(message_bytes).to_bytes(4, byteorder='big'))
            
            # Send the message
            self.writer.write(message_bytes)
            await self.writer.drain()
            
            # Read the response length
            length_bytes = await asyncio.wait_for(
                self.reader.read(4),
                timeout=self.timeout,
            )
            
            if not length_bytes:
                logger.error("Connection closed by server")
                return {'type': 'error', 'message': 'Connection closed by server'}
            
            # Convert the length bytes to an integer
            response_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read the response
            response_bytes = await asyncio.wait_for(
                self.reader.read(response_length),
                timeout=self.timeout,
            )
            
            if not response_bytes:
                logger.error("Connection closed by server")
                return {'type': 'error', 'message': 'Connection closed by server'}
            
            # Decode the response
            response = json.loads(response_bytes.decode('utf-8'))
            
            return response
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for server response after {self.timeout} seconds")
            return {'type': 'error', 'message': 'Timeout waiting for server response'}
        
        except Exception as e:
            logger.exception(f"Error sending message to server: {e}")
            return {'type': 'error', 'message': f'Error: {str(e)}'}
    
    def start_recording(self):
        """Start recording audio."""
        if self.recording:
            return
        
        self.recording = True
        
        # Open the audio stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )
        
        logger.info("Started recording")
    
    def stop_recording(self):
        """Stop recording audio."""
        if not self.recording:
            return
        
        self.recording = False
        
        # Close the audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logger.info("Stopped recording")
    
    async def record_audio(self) -> bytes:
        """
        Record audio until silence is detected.
        
        Returns
        -------
        bytes
            Recorded audio data
        """
        if not self.recording:
            self.start_recording()
        
        frames = []
        silence_frames = 0
        silence_frames_threshold = int(self.silence_duration * self.sample_rate / self.chunk_size)
        
        print("Listening... (speak now)")
        
        while self.recording:
            # Read audio data
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)
            
            # Convert to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Check if audio is silent
            if np.abs(audio_data).mean() < self.silence_threshold:
                silence_frames += 1
                if silence_frames >= silence_frames_threshold:
                    break
            else:
                silence_frames = 0
            
            # Allow other tasks to run
            await asyncio.sleep(0.01)
        
        print("Done listening")
        
        # Create a WAV file in memory
        with wave.open("temp.wav", "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        # Read the WAV file
        with open("temp.wav", "rb") as f:
            audio_data = f.read()
        
        # Clean up
        os.remove("temp.wav")
        
        return audio_data
    
    def play_audio(self, audio_data: bytes):
        """
        Play audio data.
        
        Parameters
        ----------
        audio_data : bytes
            Audio data to play
        """
        # Save the audio data to a temporary file
        with open("temp.wav", "wb") as f:
            f.write(audio_data)
        
        # Read the WAV file
        sample_rate, audio = wavfile.read("temp.wav")
        
        # Open an output stream
        output_stream = self.audio.open(
            format=self.audio.get_format_from_width(2),  # 16-bit audio
            channels=1,  # Mono
            rate=sample_rate,
            output=True,
        )
        
        # Play the audio
        output_stream.write(audio.tobytes())
        
        # Clean up
        output_stream.stop_stream()
        output_stream.close()
        os.remove("temp.wav")
    
    async def listen_for_wake_word(self):
        """Listen for the wake word."""
        if not self.recording:
            self.start_recording()
        
        self.listening_for_wake_word = True
        
        print(f"Listening for wake word: '{self.wake_word}'")
        
        # Simple wake word detection using a sliding buffer
        buffer_duration = 3  # seconds
        buffer_size = int(buffer_duration * self.sample_rate)
        audio_buffer = np.zeros(buffer_size, dtype=np.int16)
        
        while self.listening_for_wake_word and self.running:
            # Read audio data
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Convert to numpy array
            chunk = np.frombuffer(data, dtype=np.int16)
            
            # Update the buffer
            audio_buffer = np.roll(audio_buffer, -len(chunk))
            audio_buffer[-len(chunk):] = chunk
            
            # Check if the buffer contains the wake word
            # This is a simple placeholder - in a real application,
            # you would use a proper wake word detection model
            
            # For demonstration purposes, we'll just check if there's
            # a loud sound followed by silence
            if np.abs(audio_buffer).mean() > self.silence_threshold * 3:
                # Detected a loud sound, wait for confirmation
                await asyncio.sleep(0.5)
                
                # If followed by relative silence, consider it a wake word
                if np.abs(audio_buffer[-int(0.5 * self.sample_rate):]).mean() < self.silence_threshold:
                    print("Wake word detected!")
                    self.listening_for_wake_word = False
                    return True
            
            # Allow other tasks to run
            await asyncio.sleep(0.01)
        
        return False
    
    async def process_command(self):
        """Process a voice command."""
        self.processing = True
        
        try:
            # Record audio
            audio_data = await self.record_audio()
            
            # Encode audio data as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Send the audio to the server
            message = {
                'type': 'audio',
                'data': audio_base64,
            }
            
            print("Processing your request...")
            
            # Send the message to the server
            response = await self.send_message(message)
            
            if response.get('type') == 'error':
                print(f"Error: {response.get('message')}")
                return
            
            # Display the transcription
            if self.config['ui']['display_transcriptions']:
                print(f"You said: {response.get('text')}")
            
            # Display the response
            if self.config['ui']['display_responses']:
                print(f"Assistant: {response.get('response')}")
            
            # Play the response audio
            speech_base64 = response.get('speech')
            if speech_base64:
                speech_data = base64.b64decode(speech_base64)
                self.play_audio(speech_data)
            
            # Display device action if any
            device_action = response.get('device_action')
            if device_action and device_action.get('success'):
                print(f"Device action: {device_action.get('message')}")
        
        except Exception as e:
            logger.exception(f"Error processing command: {e}")
            print(f"Error processing command: {e}")
        
        finally:
            self.processing = False
    
    async def run(self):
        """Run the voice assistant client."""
        self.running = True
        
        # Connect to the server
        if not await self.connect():
            print("Failed to connect to the server. Please make sure the server is running.")
            return
        
        # Start recording
        self.start_recording()
        
        try:
            while self.running:
                # Listen for wake word
                wake_word_detected = await self.listen_for_wake_word()
                
                if wake_word_detected:
                    # Process the command
                    await self.process_command()
                    
                    # Start listening for wake word again
                    self.listening_for_wake_word = True
                
                # Allow other tasks to run
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\nStopping voice assistant...")
        
        except Exception as e:
            logger.exception(f"Error in voice assistant client: {e}")
            print(f"Error: {e}")
        
        finally:
            # Clean up
            self.running = False
            self.stop_recording()
            
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            
            self.audio.terminate()
            
            print("Voice assistant stopped")


async def main():
    """Run the voice assistant client."""
    # Get the configuration path
    config_path = os.path.join(os.path.dirname(__file__), "config", "client.yaml")
    
    # Create and run the client
    client = VoiceAssistantClient(config_path)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
