"""
ollama_integration.py
"""

"""Ollama LLM integration with MCP hardware control."""

import asyncio
import json
import logging
from typing import Dict, Any, List

import ollama
from mcp_hardware import MCPHardwareClient, MCPServer, PermissionManager
from mcp_hardware.server.gpio import GPIOServer
from mcp_hardware.server.input import InputServer


class OllamaHardwareAgent:
    """Agent that uses Ollama to control hardware through MCP."""

    def __init__(
            self,
            model: str = "llama2",
            mcp_host: str = "127.0.0.1",
            mcp_port: int = 8888
    ):
        self.model = model
        self.client = MCPHardwareClient(mcp_host, mcp_port)
        self.logger = logging.getLogger("OllamaHardwareAgent")
        self.system_prompt = """You are a hardware control agent that can interact with physical devices through MCP.

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
"""

    async def connect(self):
        """Connect to MCP server."""
        await self.client.connect()

    async def process_command(self, user_input: str) -> Dict[str, Any]:
        """Process user command using Ollama."""
        # Create conversation with Ollama
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        try:
            # Get response from Ollama
            response = ollama.chat(
                model=self.model,
                messages=messages,
                format="json"
            )

            # Parse response
            content = response['message']['content']
            command_data = json.loads(content)

            self.logger.info(f"LLM command: {command_data}")

            # Execute command
            return await self.execute_command(command_data)

        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {"error": str(e)}

    async def execute_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hardware command."""
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
            return {"error": f"Unknown command: {command}"}

        try:
            result = await command_map[command](params)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}

    async def interactive_session(self):
        """Run interactive session with user."""
        print("Ollama Hardware Control Agent")
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
        finally:
            await self.client.disconnect()


async def setup_server():
    """Setup MCP server with hardware capabilities."""
    # Create permission manager
    permission_manager = PermissionManager()

    # Allow access to all hardware for demo
    permission_manager.grant_permission("client_*", "gpio")
    permission_manager.grant_permission("client_*", "input")

    # Create server
    server = MCPServer(permission_manager=permission_manager)

    # Register hardware servers
    server.register_server("gpio", GPIOServer())
    server.register_server("input", InputServer())

    # Start server
    await server.start()


async def demo_automation():
    """Demonstrate automated hardware control with Ollama."""
    agent = OllamaHardwareAgent()
    await agent.connect()

    # Example automation scenarios
    scenarios = [
        "Setup pin 17 as output for LED control",
        "Turn on the LED connected to pin 17",
        "Blink the LED 5 times",
        "Take a screenshot and save it",
        "Type 'Hello from Ollama' using keyboard",
        "Move mouse to position 500,500 and click"
    ]

    for scenario in scenarios:
        print(f"\nExecuting: {scenario}")
        result = await agent.process_command(scenario)
        print(f"Result: {json.dumps(result, indent=2)}")
        await asyncio.sleep(2)

    await agent.client.disconnect()


async def voice_control_demo():
    """Voice control demo with speech recognition."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    agent = OllamaHardwareAgent()

    await agent.connect()

    print("Voice Control Active - Say 'exit' to quit")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)

        while True:
            try:
                print("\nListening...")
                audio = recognizer.listen(source, timeout=5)

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
                        default="interactive", help="Running mode")
    parser.add_argument("--model", default="llama2", help="Ollama model to use")

    args = parser.parse_args()

    if args.mode == "server":
        asyncio.run(setup_server())
    elif args.mode == "interactive":
        agent = OllamaHardwareAgent(model=args.model)
        asyncio.run(agent.interactive_session())
    elif args.mode == "demo":
        asyncio.run(demo_automation())
    elif args.mode == "voice":
        asyncio.run(voice_control_demo())