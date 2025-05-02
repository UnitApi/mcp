#!/usr/bin/env python3
"""
Raspberry Pi Hardware Simulator for Docker Environment

This script creates a virtual hardware server that simulates Raspberry Pi hardware devices
like GPIO, camera, and audio for testing in a Docker environment.
"""

import asyncio
import logging
import os
import sys
import signal
from typing import Dict, Any, Optional

from unitmcp.server.base import MCPHardwareServer
from unitmcp.server.gpio import GPIOServer
from unitmcp.server.camera import CameraServer
from unitmcp.server.audio import AudioServer
from unitmcp.server.input import InputServer
from unitmcp.protocols import get_llm_mcp_hardware_server

# Get the LLMMCPHardwareServer class
LLMMCPHardwareServer = get_llm_mcp_hardware_server()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RaspberryPiSimulator")

# Get environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8080'))
SERVER_NAME = os.getenv('SERVER_NAME', 'Raspberry Pi Simulator')


class RaspberryPiSimulator:
    """Raspberry Pi hardware simulator for Docker environment."""

    def __init__(self, host: str = HOST, port: int = PORT):
        """Initialize the Raspberry Pi simulator."""
        self.host = host
        self.port = port
        self.hardware_server = MCPHardwareServer(host=host, port=port)
        self.llm_server = LLMMCPHardwareServer(
            server_name=SERVER_NAME,
            rpi_host=host,
            rpi_port=port
        )
        
        # Register hardware servers
        self._register_servers()
        
        # Handle shutdown signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _register_servers(self):
        """Register hardware servers."""
        # Register GPIO server
        gpio_server = GPIOServer()
        self.hardware_server.register_server("gpio", gpio_server)
        logger.info("Registered GPIO server")
        
        # Register Camera server
        camera_server = CameraServer()
        self.hardware_server.register_server("camera", camera_server)
        logger.info("Registered Camera server")
        
        # Register Audio server
        audio_server = AudioServer()
        self.hardware_server.register_server("audio", audio_server)
        logger.info("Registered Audio server")
        
        # Register Input server
        input_server = InputServer()
        self.hardware_server.register_server("input", input_server)
        logger.info("Registered Input server")
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.hardware_server.stop()
        sys.exit(0)
    
    async def start(self):
        """Start the hardware server."""
        logger.info(f"Starting Raspberry Pi simulator on {self.host}:{self.port}")
        
        # Register custom tools for LLM server
        await self._register_custom_tools()
        
        # Start LLM MCP server in a separate thread
        import threading
        llm_thread = threading.Thread(target=self.llm_server.run)
        llm_thread.daemon = True
        llm_thread.start()
        logger.info(f"Started LLM MCP server: {SERVER_NAME}")
        
        # Start hardware server
        await self.hardware_server.start()
    
    async def _register_custom_tools(self):
        """Register custom tools for the LLM server."""
        
        @self.llm_server.register_tool
        async def led_control(pin: int, state: str) -> Dict[str, Any]:
            """
            Control an LED connected to a GPIO pin.
            
            Args:
                pin: The GPIO pin number
                state: The desired state ('on', 'off', or 'blink')
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"LED control: pin={pin}, state={state}")
            
            client = await self.llm_server.get_hardware_client()
            
            try:
                # Set up the pin as output
                await client.setup_pin(pin, "output")
                
                if state.lower() == "on":
                    await client.write_pin(pin, 1)
                    return {"success": True, "message": f"LED on pin {pin} turned on"}
                elif state.lower() == "off":
                    await client.write_pin(pin, 0)
                    return {"success": True, "message": f"LED on pin {pin} turned off"}
                elif state.lower() == "blink":
                    # Blink 3 times
                    for _ in range(3):
                        await client.write_pin(pin, 1)
                        await asyncio.sleep(0.5)
                        await client.write_pin(pin, 0)
                        await asyncio.sleep(0.5)
                    return {"success": True, "message": f"LED on pin {pin} blinked 3 times"}
                else:
                    return {"success": False, "message": f"Unknown state: {state}. Use 'on', 'off', or 'blink'"}
            except Exception as e:
                logger.error(f"Error controlling LED: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def button_read(pin: int) -> Dict[str, Any]:
            """
            Read the state of a button connected to a GPIO pin.
            
            Args:
                pin: The GPIO pin number
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Button read: pin={pin}")
            
            client = await self.llm_server.get_hardware_client()
            
            try:
                # Set up the pin as input
                await client.setup_pin(pin, "input")
                
                # Read the pin state (simulate a random button state)
                import random
                state = random.choice([0, 1])
                
                return {
                    "success": True,
                    "message": f"Button on pin {pin} state: {'pressed' if state == 1 else 'released'}",
                    "state": state
                }
            except Exception as e:
                logger.error(f"Error reading button: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def camera_capture() -> Dict[str, Any]:
            """
            Capture an image from the Raspberry Pi camera.
            
            Returns:
                A dictionary with the result of the operation
            """
            logger.info("Camera capture")
            
            try:
                # Simulate camera capture
                logger.info("Simulating camera capture")
                
                return {
                    "success": True,
                    "message": "Camera image captured",
                    "details": {
                        "width": 640,
                        "height": 480,
                        "format": "jpeg"
                    }
                }
            except Exception as e:
                logger.error(f"Error capturing camera image: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def text_to_speech(text: str) -> Dict[str, Any]:
            """
            Convert text to speech and play it on the Raspberry Pi.
            
            Args:
                text: The text to convert to speech
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Text to speech: text='{text}'")
            
            try:
                # Simulate text-to-speech
                logger.info(f"Simulating TTS for: '{text}'")
                
                return {
                    "success": True,
                    "message": f"Text played as speech: '{text}'",
                    "details": {
                        "duration": len(text) * 0.1,  # Rough estimate of speech duration
                        "text": text
                    }
                }
            except Exception as e:
                logger.error(f"Error playing text as speech: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def audio_record(duration: int = 3) -> Dict[str, Any]:
            """
            Record audio from the Raspberry Pi microphone.
            
            Args:
                duration: Recording duration in seconds
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Audio record: duration={duration}")
            
            try:
                # Simulate audio recording
                logger.info(f"Simulating audio recording for {duration} seconds")
                await asyncio.sleep(duration)
                
                return {
                    "success": True,
                    "message": f"Audio recorded for {duration} seconds",
                    "details": {
                        "duration": duration,
                        "sample_rate": 44100,
                        "channels": 1
                    }
                }
            except Exception as e:
                logger.error(f"Error recording audio: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def temperature_read() -> Dict[str, Any]:
            """
            Read the temperature from a simulated sensor.
            
            Returns:
                A dictionary with the result of the operation
            """
            logger.info("Temperature read")
            
            try:
                # Simulate temperature reading
                import random
                temperature = round(random.uniform(20.0, 30.0), 1)
                
                return {
                    "success": True,
                    "message": f"Temperature: {temperature}°C",
                    "temperature": temperature
                }
            except Exception as e:
                logger.error(f"Error reading temperature: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}


def main():
    """Main function."""
    simulator = RaspberryPiSimulator(host=HOST, port=PORT)
    
    try:
        # Start the simulator
        asyncio.run(simulator.start())
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    except Exception as e:
        logger.error(f"Simulator error: {e}")


if __name__ == "__main__":
    main()
