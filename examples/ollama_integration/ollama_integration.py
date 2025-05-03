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
    from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
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
        from unitmcp.utils import EnvLoader, get_rpi_host, get_rpi_port, get_simulation_mode
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
        self.host = mcp_host or get_rpi_host()
        self.port = mcp_port or get_rpi_port()
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

    async def interactive_session(self):
        """Run interactive session with user."""
        print("Ollama Hardware Control Agent")
        print(f"Using model: {self.model}")
        print(f"Connected to MCP server at {self.host}:{self.port}")
        print("Type 'exit' to quit")
        print("-" * 30)

        try:
            await self.connect()

            while True:
                user_input = input("\nYour command: ")

                if user_input.lower() in ['exit', 'quit']:
                    break

                result = await self.process_command(user_input)
                print(f"Result: {json.dumps(result, indent=2)}")

        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            await self.client.disconnect()
            print("Disconnected from MCP server")


async def setup_server():
    """Setup MCP server with hardware capabilities."""
    # Get configuration from environment variables
    server_host = env.get('SERVER_HOST', '0.0.0.0')
    server_port = env.get_int('SERVER_PORT', 8080)
    
    # Create permission manager
    permission_manager = PermissionManager()

    # Allow access to all hardware for demo
    permission_manager.grant_permission("client_*", "gpio")
    permission_manager.grant_permission("client_*", "input")

    # Create server
    server = MCPServer(
        host=server_host,
        port=server_port,
        permission_manager=permission_manager
    )

    # Register hardware servers
    server.register_server("gpio", GPIOServer())
    server.register_server("input", InputServer())

    # Start server
    print(f"Starting MCP server on {server_host}:{server_port}")
    await server.start()


async def demo_automation():
    """Demonstrate automated hardware control with Ollama."""
    # Get configuration from environment variables
    model = env.get('OLLAMA_MODEL', 'llama2')
    
    agent = OllamaHardwareAgent(model=model)
    await agent.connect()

    # Example automation scenarios
    scenarios = env.get_list('DEMO_SCENARIOS', [
        "Setup pin 17 as output for LED control",
        "Turn on the LED connected to pin 17",
        "Blink the LED 5 times",
        "Take a screenshot and save it",
        "Type 'Hello from Ollama' using keyboard",
        "Move mouse to position 500,500 and click"
    ])

    for scenario in scenarios:
        print(f"\nExecuting: {scenario}")
        result = await agent.process_command(scenario)
        print(f"Result: {json.dumps(result, indent=2)}")
        await asyncio.sleep(env.get_float('DEMO_DELAY', 2.0))

    await agent.client.disconnect()


async def voice_control_demo():
    """Voice control demo with speech recognition."""
    try:
        import speech_recognition as sr
    except ImportError:
        print("Speech recognition not found, trying to install...")
        os.system(f"{sys.executable} -m pip install SpeechRecognition")
        import speech_recognition as sr

    # Get configuration from environment variables
    model = env.get('OLLAMA_MODEL', 'llama2')
    timeout = env.get_float('VOICE_TIMEOUT', 5.0)
    
    recognizer = sr.Recognizer()
    agent = OllamaHardwareAgent(model=model)

    await agent.connect()

    print("Voice Control Active - Say 'exit' to quit")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)

        while True:
            try:
                print("\nListening...")
                audio = recognizer.listen(source, timeout=timeout)

                # Convert speech to text
                command = recognizer.recognize_google(audio)
                print(f"You said: {command}")

                if "exit" in command.lower():
                    break

                # Process command
                result = await agent.process_command(command)
                print(f"Result: {json.dumps(result, indent=2)}")

            except sr.WaitTimeoutError:
                print("No speech detected")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except Exception as e:
                print(f"Error: {e}")

    await agent.client.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ollama Hardware Control")
    parser.add_argument("--mode", choices=["server", "interactive", "demo", "voice"],
                        default=env.get('OLLAMA_MODE', 'interactive'), 
                        help="Running mode")
    parser.add_argument("--model", default=env.get('OLLAMA_MODEL', 'llama2'), 
                        help="Ollama model to use")
    parser.add_argument("--host", default=env.get('RPI_HOST', None),
                        help="MCP server hostname or IP")
    parser.add_argument("--port", type=int, default=env.get_int('RPI_PORT', None),
                        help="MCP server port")
    parser.add_argument("--env-file", default=None,
                        help="Path to custom .env file")

    args = parser.parse_args()
    
    # Load custom environment file if specified
    if args.env_file:
        env = EnvLoader(args.env_file)
    
    # Check if simulation mode is enabled
    simulation = get_simulation_mode()
    if simulation:
        print("Running in simulation mode - no actual hardware will be controlled")

    if args.mode == "server":
        asyncio.run(setup_server())
    elif args.mode == "interactive":
        agent = OllamaHardwareAgent(model=args.model, mcp_host=args.host, mcp_port=args.port)
        asyncio.run(agent.interactive_session())
    elif args.mode == "demo":
        asyncio.run(demo_automation())
    elif args.mode == "voice":
        asyncio.run(voice_control_demo())