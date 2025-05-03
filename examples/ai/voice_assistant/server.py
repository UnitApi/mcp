#!/usr/bin/env python3
"""
Voice Assistant Server

This script implements the server-side of the voice assistant example.
It handles speech-to-text, natural language processing, language model
responses, text-to-speech, and hardware control.
"""

import asyncio
import json
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.unitmcp.utils.env_loader import EnvLoader
from src.unitmcp.ai import (
    # LLM models
    ollama, claude, openai,
    
    # Speech models
    STTModel, WhisperConfig, WhisperModel, GoogleSpeechConfig, GoogleSpeechModel,
    TTSModel, PyTTSX3Config, PyTTSX3Model, GTTSConfig, GTTSModel,
    
    # NLP models
    SpacyConfig, SpacyNLPModel, HuggingFaceConfig, HuggingFaceNLPModel,
)
from src.unitmcp.platforms.adapters.platform_adapter import get_platform_adapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VoiceAssistantServer:
    """
    Server for the voice assistant example.
    
    This class handles:
    - WebSocket connections from clients
    - Speech-to-text processing
    - Natural language understanding
    - Language model responses
    - Text-to-speech conversion
    - Hardware control
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the voice assistant server.
        
        Parameters
        ----------
        config_path : str
            Path to the server configuration file
        """
        self.config = self._load_config(config_path)
        self.clients = set()
        self.llm = None
        self.stt = None
        self.tts = None
        self.nlp = None
        self.platform_adapter = None
        self.running = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the server configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
            
        Returns
        -------
        Dict[str, Any]
            Server configuration
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    async def initialize(self) -> bool:
        """
        Initialize the AI models and hardware control.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize the language model
            llm_config = self.config['ai']['llm']
            llm_provider = llm_config['provider']
            
            if llm_provider == 'ollama':
                ollama_config = ollama.OllamaConfig(
                    model=llm_config['model'],
                    host=os.environ.get('OLLAMA_HOST', 'localhost'),
                    port=int(os.environ.get('OLLAMA_PORT', '11434')),
                )
                self.llm = ollama.OllamaModel("voice-assistant-llm", ollama_config)
            
            elif llm_provider == 'claude':
                claude_config = claude.ClaudeConfig(
                    model=llm_config['model'],
                    api_key=os.environ.get('ANTHROPIC_API_KEY'),
                )
                self.llm = claude.ClaudeModel("voice-assistant-llm", claude_config)
            
            elif llm_provider == 'openai':
                openai_config = openai.OpenAIConfig(
                    model=llm_config['model'],
                    api_key=os.environ.get('OPENAI_API_KEY'),
                )
                self.llm = openai.OpenAIModel("voice-assistant-llm", openai_config)
            
            else:
                logger.error(f"Unsupported LLM provider: {llm_provider}")
                return False
            
            # Initialize the LLM
            if not await self.llm.initialize():
                logger.error(f"Failed to initialize {llm_provider} model")
                return False
            
            # Initialize the speech-to-text model
            stt_config = self.config['ai']['stt']
            stt_provider = stt_config['provider']
            
            if stt_provider == 'whisper':
                whisper_config = WhisperConfig(
                    model_size=stt_config['model'],
                    language=stt_config['language'],
                )
                self.stt = WhisperModel("voice-assistant-stt", whisper_config)
            
            elif stt_provider == 'google_speech':
                google_config = GoogleSpeechConfig(
                    language=stt_config['language'],
                    api_key=os.environ.get('GOOGLE_API_KEY'),
                )
                self.stt = GoogleSpeechModel("voice-assistant-stt", google_config)
            
            else:
                logger.error(f"Unsupported STT provider: {stt_provider}")
                return False
            
            # Initialize the STT model
            if not await self.stt.initialize():
                logger.error(f"Failed to initialize {stt_provider} model")
                return False
            
            # Initialize the text-to-speech model
            tts_config = self.config['ai']['tts']
            tts_provider = tts_config['provider']
            
            if tts_provider == 'pyttsx3':
                pyttsx3_config = PyTTSX3Config(
                    voice=tts_config['voice'],
                    rate=tts_config['rate'],
                    volume=tts_config['volume'],
                )
                self.tts = PyTTSX3Model("voice-assistant-tts", pyttsx3_config)
            
            elif tts_provider == 'gtts':
                gtts_config = GTTSConfig(
                    language=self.config['ai']['stt']['language'][:2],  # Extract language code (e.g., 'en' from 'en-US')
                    slow=False,
                )
                self.tts = GTTSModel("voice-assistant-tts", gtts_config)
            
            else:
                logger.error(f"Unsupported TTS provider: {tts_provider}")
                return False
            
            # Initialize the TTS model
            if not await self.tts.initialize():
                logger.error(f"Failed to initialize {tts_provider} model")
                return False
            
            # Initialize the NLP model
            nlp_config = self.config['ai']['nlp']
            nlp_provider = nlp_config['provider']
            
            if nlp_provider == 'spacy':
                spacy_config = SpacyConfig(
                    model_name=nlp_config['model'],
                )
                self.nlp = SpacyNLPModel("voice-assistant-nlp", spacy_config)
            
            elif nlp_provider == 'huggingface':
                hf_config = HuggingFaceConfig(
                    model_name=nlp_config['model'],
                    task="token-classification" if nlp_config.get('extract_entities', True) else "text-classification",
                )
                self.nlp = HuggingFaceNLPModel("voice-assistant-nlp", hf_config)
            
            else:
                logger.error(f"Unsupported NLP provider: {nlp_provider}")
                return False
            
            # Initialize the NLP model
            if not await self.nlp.initialize():
                logger.error(f"Failed to initialize {nlp_provider} model")
                return False
            
            # Initialize hardware control if enabled
            if self.config['hardware']['enabled']:
                platform = self.config['hardware']['platform']
                
                # Get the platform adapter
                self.platform_adapter = get_platform_adapter(platform)
                
                if not self.platform_adapter:
                    logger.error(f"Failed to get platform adapter for {platform}")
                    return False
                
                # Initialize the platform adapter
                if not await self.platform_adapter.initialize():
                    logger.error(f"Failed to initialize platform adapter for {platform}")
                    return False
                
                logger.info(f"Initialized hardware control for {platform}")
            
            logger.info("Server initialization complete")
            return True
        
        except Exception as e:
            logger.exception(f"Error initializing server: {e}")
            return False
    
    async def start(self):
        """Start the WebSocket server."""
        server_config = self.config['server']
        host = server_config['host']
        port = server_config['port']
        
        # Initialize the server
        if not await self.initialize():
            logger.error("Failed to initialize server, exiting")
            return
        
        # Start the WebSocket server
        self.running = True
        
        try:
            server = await asyncio.start_server(
                self.handle_client,
                host,
                port,
            )
            
            logger.info(f"Server started on {host}:{port}")
            
            async with server:
                await server.serve_forever()
        
        except Exception as e:
            logger.exception(f"Error starting server: {e}")
            self.running = False
    
    async def handle_client(self, reader, writer):
        """
        Handle a client connection.
        
        Parameters
        ----------
        reader : asyncio.StreamReader
            Stream reader for the client connection
        writer : asyncio.StreamWriter
            Stream writer for the client connection
        """
        addr = writer.get_extra_info('peername')
        logger.info(f"New client connected: {addr}")
        
        # Add the client to the set of connected clients
        client = (reader, writer)
        self.clients.add(client)
        
        try:
            while self.running:
                # Read the message length (4 bytes)
                length_bytes = await reader.read(4)
                if not length_bytes:
                    break
                
                # Convert the length bytes to an integer
                message_length = int.from_bytes(length_bytes, byteorder='big')
                
                # Read the message
                message_bytes = await reader.read(message_length)
                if not message_bytes:
                    break
                
                # Decode the message
                message = json.loads(message_bytes.decode('utf-8'))
                
                # Process the message
                response = await self.process_message(message)
                
                # Encode the response
                response_bytes = json.dumps(response).encode('utf-8')
                
                # Send the response length
                writer.write(len(response_bytes).to_bytes(4, byteorder='big'))
                
                # Send the response
                writer.write(response_bytes)
                await writer.drain()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f"Error handling client {addr}: {e}")
        
        finally:
            # Remove the client from the set of connected clients
            self.clients.remove(client)
            
            # Close the connection
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Client disconnected: {addr}")
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message from a client.
        
        Parameters
        ----------
        message : Dict[str, Any]
            Message from the client
            
        Returns
        -------
        Dict[str, Any]
            Response to the client
        """
        message_type = message.get('type')
        
        if message_type == 'audio':
            # Process audio data
            audio_data = message.get('data')
            
            # Convert audio data from base64 to bytes
            import base64
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert speech to text
            text = await self.stt.speech_to_text(audio_bytes)
            
            # Process the text with NLP
            nlp_result = await self.nlp.process(text)
            
            # Extract entities
            entities = nlp_result.get('entities', [])
            
            # Check if this is a device control command
            is_device_command = await self.is_device_control_command(text, entities)
            
            # Generate a response using the LLM
            llm_response = await self.generate_response(text, entities, is_device_command)
            
            # Convert the response to speech
            speech_bytes = await self.tts.text_to_speech(llm_response)
            
            # Convert speech bytes to base64
            speech_base64 = base64.b64encode(speech_bytes).decode('utf-8')
            
            # If this is a device control command, execute it
            device_action = None
            if is_device_command:
                device_action = await self.execute_device_command(text, entities)
            
            return {
                'type': 'response',
                'text': text,
                'response': llm_response,
                'speech': speech_base64,
                'entities': entities,
                'device_action': device_action,
            }
        
        elif message_type == 'text':
            # Process text input
            text = message.get('data')
            
            # Process the text with NLP
            nlp_result = await self.nlp.process(text)
            
            # Extract entities
            entities = nlp_result.get('entities', [])
            
            # Check if this is a device control command
            is_device_command = await self.is_device_control_command(text, entities)
            
            # Generate a response using the LLM
            llm_response = await self.generate_response(text, entities, is_device_command)
            
            # Convert the response to speech
            speech_bytes = await self.tts.text_to_speech(llm_response)
            
            # Convert speech bytes to base64
            import base64
            speech_base64 = base64.b64encode(speech_bytes).decode('utf-8')
            
            # If this is a device control command, execute it
            device_action = None
            if is_device_command:
                device_action = await self.execute_device_command(text, entities)
            
            return {
                'type': 'response',
                'text': text,
                'response': llm_response,
                'speech': speech_base64,
                'entities': entities,
                'device_action': device_action,
            }
        
        else:
            # Unknown message type
            return {
                'type': 'error',
                'message': f"Unknown message type: {message_type}",
            }
    
    async def is_device_control_command(self, text: str, entities: List[Dict[str, Any]]) -> bool:
        """
        Check if a text is a device control command.
        
        Parameters
        ----------
        text : str
            Input text
        entities : List[Dict[str, Any]]
            Extracted entities
            
        Returns
        -------
        bool
            True if the text is a device control command, False otherwise
        """
        # Check if device control is enabled
        if not self.config['commands']['devices']['enabled']:
            return False
        
        # Get the command prefix
        command_prefix = self.config['commands']['devices']['command_prefix'].lower()
        
        # Check if the text contains the command prefix
        if command_prefix not in text.lower():
            return False
        
        # Get the list of locations and device types
        locations = self.config['commands']['devices']['locations']
        device_types = self.config['commands']['devices']['device_types']
        
        # Check if the text contains a location and a device type
        has_location = any(location.lower() in text.lower() for location in locations)
        has_device = any(device.lower() in text.lower() for device in device_types)
        
        return has_location and has_device
    
    async def execute_device_command(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a device control command.
        
        Parameters
        ----------
        text : str
            Input text
        entities : List[Dict[str, Any]]
            Extracted entities
            
        Returns
        -------
        Dict[str, Any]
            Result of the command execution
        """
        # Check if hardware control is enabled
        if not self.config['hardware']['enabled'] or not self.platform_adapter:
            return {
                'success': False,
                'message': "Hardware control is not enabled",
            }
        
        # Get the command prefix, locations, and device types
        command_prefix = self.config['commands']['devices']['command_prefix'].lower()
        locations = self.config['commands']['devices']['locations']
        device_types = self.config['commands']['devices']['device_types']
        
        # Extract the action (on/off)
        action = "on" if "on" in text.lower() else "off"
        
        # Extract the location
        location = None
        for loc in locations:
            if loc.lower() in text.lower():
                location = loc
                break
        
        # Extract the device type
        device_type = None
        for dev in device_types:
            if dev.lower() in text.lower():
                device_type = dev
                break
        
        if not location or not device_type:
            return {
                'success': False,
                'message': "Could not extract location or device type",
            }
        
        # Get the GPIO pin for the device
        pin_key = f"{location.lower().replace(' ', '_')}_{device_type.lower().replace(' ', '_')}"
        pin = self.config['hardware']['gpio_pins'].get(pin_key)
        
        if not pin:
            return {
                'success': False,
                'message': f"No GPIO pin configured for {location} {device_type}",
            }
        
        try:
            # Execute the command
            if action == "on":
                await self.platform_adapter.set_pin(pin, True)
            else:
                await self.platform_adapter.set_pin(pin, False)
            
            return {
                'success': True,
                'message': f"Turned {action} the {device_type} in the {location}",
                'device': device_type,
                'location': location,
                'action': action,
                'pin': pin,
            }
        
        except Exception as e:
            logger.exception(f"Error executing device command: {e}")
            return {
                'success': False,
                'message': f"Error executing command: {str(e)}",
            }
    
    async def generate_response(self, text: str, entities: List[Dict[str, Any]], is_device_command: bool) -> str:
        """
        Generate a response using the language model.
        
        Parameters
        ----------
        text : str
            Input text
        entities : List[Dict[str, Any]]
            Extracted entities
        is_device_command : bool
            Whether the input is a device control command
            
        Returns
        -------
        str
            Generated response
        """
        # Create the prompt for the language model
        system_prompt = self.config['ai']['llm']['system_prompt']
        
        # Add context about the entities
        entity_context = ""
        if entities:
            entity_context = "Entities detected: " + ", ".join([f"{e['text']} ({e['label']})" for e in entities])
        
        # Add context about device control
        device_context = ""
        if is_device_command:
            device_context = "This appears to be a device control command."
        
        # Combine the prompts
        prompt = f"{text}\n\n{entity_context}\n{device_context}"
        
        # Generate a response
        response = await self.llm.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=self.config['ai']['llm']['temperature'],
            max_tokens=self.config['ai']['llm']['max_tokens'],
        )
        
        return response
    
    async def cleanup(self):
        """Clean up resources."""
        self.running = False
        
        # Close all client connections
        for reader, writer in self.clients:
            writer.close()
        
        # Clean up AI models
        if self.llm:
            await self.llm.cleanup()
        
        if self.stt:
            await self.stt.cleanup()
        
        if self.tts:
            await self.tts.cleanup()
        
        if self.nlp:
            await self.nlp.cleanup()
        
        # Clean up hardware control
        if self.platform_adapter:
            await self.platform_adapter.cleanup()
        
        logger.info("Server cleanup complete")


async def main():
    """Run the voice assistant server."""
    # Load environment variables
    env_loader = EnvLoader()
    env_loader.load_env()
    
    # Get the configuration path
    config_path = os.path.join(os.path.dirname(__file__), "config", "server.yaml")
    
    # Create and start the server
    server = VoiceAssistantServer(config_path)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
