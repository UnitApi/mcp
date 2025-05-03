#!/usr/bin/env python3
"""
Ollama LLM integration with UnitMCP hardware control.

This example demonstrates how to use Ollama language models to control
hardware through the UnitMCP library. It supports various modes of operation
and can be configured using environment variables.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import ollama
except ImportError:
    print("Ollama not found, trying to install...")
    os.system(f"{sys.executable} -m pip install ollama")
    import ollama

try:
    from unitmcp import MCPHardwareClient, MCPServer
    from unitmcp.server.gpio import GPIOServer
    from unitmcp.server.input import InputServer
    from unitmcp.server.permission import PermissionManager
    from unitmcp.utils import EnvLoader
except ImportError:
    print("Error: Could not import unitmcp module.")
    print(f"Make sure the UnitMCP project is in your Python path.")
    print(f"Current Python path: {sys.path}")
    print(f"Trying to add {os.path.join(project_root, 'src')} to Python path...")
    sys.path.insert(0, os.path.join(project_root, 'src'))
    try:
        from unitmcp import MCPHardwareClient, MCPServer
        from unitmcp.server.gpio import GPIOServer
        from unitmcp.server.input import InputServer
        from unitmcp.server.permission import PermissionManager
        from unitmcp.utils import EnvLoader
        print("Successfully imported unitmcp module after path adjustment.")
    except ImportError:
        print("Failed to import unitmcp module even after path adjustment.")
        sys.exit(1)

# Load environment variables
env = EnvLoader()

# Configure logging
logging.basicConfig(
    level=env.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OllamaHardwareAgent:
    """Agent that uses Ollama to control hardware through UnitMCP."""

    def __init__(
            self,
            model: str = None,
            mcp_host: str = None,
            mcp_port: int = None
    ):
        """
        Initialize the Ollama Hardware Agent.
        
        Args:
            model: Ollama model to use
            mcp_host: Host for the MCP server
            mcp_port: Port for the MCP server
        """
        self.model = model or env.get('OLLAMA_MODEL', 'llama2')
        self.host = mcp_host or env.get('RPI_HOST', 'localhost')
        self.port = mcp_port or env.get_int('RPI_PORT', 8080)
        self.client = MCPHardwareClient(self.host, self.port)
        self.logger = logging.getLogger("OllamaHardwareAgent")
        
        # Get system prompt from environment or use default
        self.system_prompt = env.get('OLLAMA_SYSTEM_PROMPT', """You are a hardware control agent that can interact with physical devices through MCP.

Available commands:
1. GPIO control:
   - setup_pin(pin, mode): Setup GPIO pin as INPUT or OUTPUT
   - write_pin(pin, value): Write HIGH (1) or LOW (0) to pin
   - read_pin(pin): Read pin value
   - setup_led(device_id, pin): Setup LED on pin
   - control_led(device_id, action): Control LED (on/off/blink)

2. Input control:
   - type_text(text): Type text using keyboard
   - move_mouse(x, y): Move mouse to coordinates
   - click(button): Perform mouse click
   - screenshot(): Take a screenshot

Respond with JSON containing the command and parameters.
Example: {"command": "setup_pin", "params": {"pin": 17, "mode": "OUT"}}
""")

    async def connect(self):
        """Connect to MCP server."""
        try:
            self.logger.info(f"Connecting to MCP server at {self.host}:{self.port}")
            await self.client.connect()
            self.logger.info("Connected to MCP server successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def process_command(self, user_input: str) -> Dict[str, Any]:
        """
        Process user command using Ollama.
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Dictionary with command result
        """
        # Create conversation with Ollama
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        try:
            # Get response from Ollama
            self.logger.info(f"Sending request to Ollama model: {self.model}")
            response = ollama.chat(
                model=self.model,
                messages=messages,
                format="json"
            )

            # Parse response
            content = response['message']['content']
            self.logger.debug(f"Ollama response: {content}")
            
            try:
                command_data = json.loads(content)
                self.logger.info(f"LLM command: {command_data}")

                # Execute command
                return await self.execute_command(command_data)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON from Ollama response: {content}")
                return {"error": "Invalid JSON response from Ollama"}

        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {"error": str(e)}

    async def execute_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute hardware command.
        
        Args:
            command_data: Dictionary with command and parameters
            
        Returns:
            Dictionary with execution result
        """
        command = command_data.get("command")
        params = command_data.get("params", {})

        # Map commands to client methods
        command_map = {
            "setup_pin": lambda p: self.client.setup_pin(p["pin"], p.get("mode", "OUT")),
            "write_pin": lambda p: self.client.write_pin(p["pin"], p["value"]),
            "read_pin": lambda p: self.client.read_pin(p["pin"]),
            "setup_led": lambda p: self.client.setup_led(p["device_id"], p["pin"]),
            "control_led": lambda p: self.client.control_led(
                p["device_id"],
                p["action"],
                **{k: v for k, v in p.items() if k not in ["device_id", "action"]}
            ),
            "type_text": lambda p: self.client.type_text(p["text"]),
            "move_mouse": lambda p: self.client.move_mouse(p["x"], p["y"]),
            "click": lambda p: self.client.click(p.get("button", "left")),
            "screenshot": lambda p: self.client.screenshot()
        }

        if command not in command_map:
            self.logger.error(f"Unknown command: {command}")
            return {"error": f"Unknown command: {command}"}

        try:
            self.logger.info(f"Executing command: {command} with params: {params}")
            result = await command_map[command](params)
            self.logger.info(f"Command executed successfully: {result}")
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the connection to the MCP server."""
        try:
            await self.client.disconnect()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Error disconnecting from MCP server: {e}")

    async def interactive_session(self):
        """Run an interactive session with the agent."""
        print(f"Ollama Hardware Agent - Model: {self.model}")
        print("Type 'exit' or 'quit' to end the session")
        print("=" * 50)
        
        try:
            await self.connect()
            
            while True:
                user_input = input("\nEnter command: ")
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                    
                print("Processing...")
                result = await self.process_command(user_input)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"Success: {json.dumps(result.get('result', {}), indent=2)}")
                    
        finally:
            await self.close()


async def setup_server(host: str = None, port: int = None):
    """
    Setup MCP server with hardware capabilities.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
    """
    host = host or env.get('RPI_HOST', 'localhost')
    port = port or env.get_int('RPI_PORT', 8080)
    
    # Create server with GPIO and input capabilities
    server = MCPServer(host, port)
    
    # Add GPIO server
    gpio_server = GPIOServer()
    server.add_server(gpio_server)
    
    # Add input server
    input_server = InputServer()
    server.add_server(input_server)
    
    # Configure permissions
    permission_manager = PermissionManager()
    permission_manager.allow_all()  # For demo purposes
    server.set_permission_manager(permission_manager)
    
    # Start server
    await server.start()
    print(f"MCP Server running at {host}:{port}")
    
    return server


async def demo_automation():
    """Demonstrate automated hardware control with Ollama."""
    print("Ollama Hardware Automation Demo")
    print("=" * 50)
    
    # Create agent
    agent = OllamaHardwareAgent(
        model=env.get('OLLAMA_MODEL', 'llama2'),
        mcp_host=env.get('RPI_HOST', 'localhost'),
        mcp_port=env.get_int('RPI_PORT', 8080)
    )
    
    try:
        await agent.connect()
        
        # Run a sequence of commands
        commands = [
            "Set up an LED on pin 17 and call it main_led",
            "Blink the main_led with 0.2 second intervals",
            "Wait for 5 seconds then turn off the main_led",
            "Move the mouse to position x=500, y=500",
            "Take a screenshot"
        ]
        
        for i, command in enumerate(commands):
            print(f"\nStep {i+1}: {command}")
            result = await agent.process_command(command)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Success: {json.dumps(result.get('result', {}), indent=2)}")
                
            # Add a small delay between commands
            await asyncio.sleep(1)
            
    finally:
        await agent.close()


async def voice_control_demo():
    """Voice control demo with speech recognition."""
    try:
        import speech_recognition as sr
        from gtts import gTTS
        import pygame
    except ImportError:
        print("Voice control dependencies not installed.")
        print("Install with: pip install SpeechRecognition gTTS pygame")
        return
    
    print("Ollama Voice Control Demo")
    print("=" * 50)
    
    # Create agent
    agent = OllamaHardwareAgent(
        model=env.get('OLLAMA_MODEL', 'llama2'),
        mcp_host=env.get('RPI_HOST', 'localhost'),
        mcp_port=env.get_int('RPI_PORT', 8080)
    )
    
    # Initialize speech recognition
    recognizer = sr.Recognizer()
    
    # Initialize pygame for audio playback
    pygame.mixer.init()
    
    def speak(text):
        """Convert text to speech and play it."""
        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    
    try:
        await agent.connect()
        speak("Voice control ready. Please speak a command.")
        
        while True:
            with sr.Microphone() as source:
                print("\nListening...")
                audio = recognizer.listen(source)
                
            try:
                command = recognizer.recognize_google(audio)
                print(f"You said: {command}")
                
                if command.lower() in ["exit", "quit", "stop"]:
                    speak("Goodbye!")
                    break
                
                speak(f"Processing command: {command}")
                result = await agent.process_command(command)
                
                if "error" in result:
                    speak(f"Error: {result['error']}")
                else:
                    speak("Command executed successfully")
                
            except sr.UnknownValueError:
                speak("Sorry, I didn't understand that.")
            except sr.RequestError:
                speak("Sorry, I couldn't request results from the speech recognition service.")
                
    finally:
        await agent.close()
        # Clean up temporary files
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Hardware Control Demo")
    parser.add_argument("--server", action="store_true", help="Run MCP server")
    parser.add_argument("--interactive", action="store_true", help="Run interactive session")
    parser.add_argument("--demo", action="store_true", help="Run automation demo")
    parser.add_argument("--voice", action="store_true", help="Run voice control demo")
    parser.add_argument("--model", type=str, help="Ollama model to use")
    parser.add_argument("--host", type=str, help="MCP server host")
    parser.add_argument("--port", type=int, help="MCP server port")
    
    args = parser.parse_args()
    
    # Override environment variables with command line arguments
    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model
    if args.host:
        os.environ["RPI_HOST"] = args.host
    if args.port:
        os.environ["RPI_PORT"] = str(args.port)
    
    # Default to interactive mode if no mode specified
    if not (args.server or args.interactive or args.demo or args.voice):
        args.interactive = True
    
    async def main():
        server = None
        
        try:
            if args.server:
                server = await setup_server()
            
            if args.interactive:
                agent = OllamaHardwareAgent()
                await agent.interactive_session()
            
            if args.demo:
                await demo_automation()
            
            if args.voice:
                await voice_control_demo()
                
            # If server is running, keep it alive
            if server:
                print("Server running. Press Ctrl+C to stop.")
                while True:
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            if server:
                await server.stop()
                print("Server stopped.")
    
    asyncio.run(main())