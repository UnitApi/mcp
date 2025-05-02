#!/usr/bin/env python3
"""
Virtual Hardware Server for Docker Environment

This script creates a virtual hardware server that simulates hardware devices
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
logger = logging.getLogger("VirtualHardwareServer")

# Get environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8080'))
SERVER_NAME = os.getenv('SERVER_NAME', 'Virtual Hardware Server')


class VirtualHardwareServer:
    """Virtual hardware server for Docker environment."""

    def __init__(self, host: str = HOST, port: int = PORT):
        """Initialize the virtual hardware server."""
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
        logger.info(f"Starting virtual hardware server on {self.host}:{self.port}")
        
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
        async def virtual_led_control(pin: int, state: str) -> Dict[str, Any]:
            """
            Control a virtual LED.
            
            Args:
                pin: The GPIO pin number
                state: The desired state ('on', 'off', or 'blink')
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Virtual LED control: pin={pin}, state={state}")
            
            client = await self.llm_server.get_hardware_client()
            
            try:
                # Set up the pin as output
                await client.setup_pin(pin, "output")
                
                if state.lower() == "on":
                    await client.write_pin(pin, 1)
                    return {"success": True, "message": f"Virtual LED on pin {pin} turned on"}
                elif state.lower() == "off":
                    await client.write_pin(pin, 0)
                    return {"success": True, "message": f"Virtual LED on pin {pin} turned off"}
                elif state.lower() == "blink":
                    # Blink 3 times
                    for _ in range(3):
                        await client.write_pin(pin, 1)
                        await asyncio.sleep(0.5)
                        await client.write_pin(pin, 0)
                        await asyncio.sleep(0.5)
                    return {"success": True, "message": f"Virtual LED on pin {pin} blinked 3 times"}
                else:
                    return {"success": False, "message": f"Unknown state: {state}. Use 'on', 'off', or 'blink'"}
            except Exception as e:
                logger.error(f"Error controlling virtual LED: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def virtual_button_press(pin: int, duration: float = 0.5) -> Dict[str, Any]:
            """
            Simulate a button press on a virtual button.
            
            Args:
                pin: The GPIO pin number
                duration: The duration of the button press in seconds
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Virtual button press: pin={pin}, duration={duration}")
            
            client = await self.llm_server.get_hardware_client()
            
            try:
                # Set up the pin as input
                await client.setup_pin(pin, "input")
                
                # Simulate button press (in a real environment, this would be a physical button)
                logger.info(f"Button on pin {pin} pressed for {duration} seconds")
                await asyncio.sleep(duration)
                logger.info(f"Button on pin {pin} released")
                
                return {
                    "success": True,
                    "message": f"Virtual button on pin {pin} pressed for {duration} seconds"
                }
            except Exception as e:
                logger.error(f"Error simulating button press: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def virtual_camera_capture() -> Dict[str, Any]:
            """
            Capture an image from a virtual camera.
            
            Returns:
                A dictionary with the result of the operation
            """
            logger.info("Virtual camera capture")
            
            client = await self.llm_server.get_hardware_client()
            
            try:
                # In a real environment, this would capture from a physical camera
                # Here we just simulate the operation
                logger.info("Simulating camera capture")
                
                return {
                    "success": True,
                    "message": "Virtual camera image captured",
                    "details": {
                        "width": 640,
                        "height": 480,
                        "format": "jpeg"
                    }
                }
            except Exception as e:
                logger.error(f"Error capturing virtual camera image: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def virtual_audio_play(text: str) -> Dict[str, Any]:
            """
            Play audio from text using text-to-speech.
            
            Args:
                text: The text to convert to speech
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Virtual audio play: text='{text}'")
            
            try:
                # In a real environment, this would use a text-to-speech engine
                # Here we just simulate the operation
                logger.info(f"Simulating TTS for: '{text}'")
                
                return {
                    "success": True,
                    "message": f"Virtual audio played: '{text}'",
                    "details": {
                        "duration": len(text) * 0.1,  # Rough estimate of speech duration
                        "text": text
                    }
                }
            except Exception as e:
                logger.error(f"Error playing virtual audio: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
        
        @self.llm_server.register_tool
        async def virtual_audio_record(duration: int = 3) -> Dict[str, Any]:
            """
            Record audio from a virtual microphone.
            
            Args:
                duration: Recording duration in seconds
                
            Returns:
                A dictionary with the result of the operation
            """
            logger.info(f"Virtual audio record: duration={duration}")
            
            try:
                # In a real environment, this would record from a physical microphone
                # Here we just simulate the operation
                logger.info(f"Simulating audio recording for {duration} seconds")
                await asyncio.sleep(duration)
                
                return {
                    "success": True,
                    "message": f"Virtual audio recorded for {duration} seconds",
                    "details": {
                        "duration": duration,
                        "sample_rate": 44100,
                        "channels": 1
                    }
                }
            except Exception as e:
                logger.error(f"Error recording virtual audio: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}


def main():
    """Main function."""
    server = VirtualHardwareServer(host=HOST, port=PORT)
    
    try:
        # Start the server
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
