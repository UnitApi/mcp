"""
voice_assistant.py
"""

"""Voice-controlled hardware assistant example."""

import asyncio
import json
import logging
import time
from typing import Dict, Any

try:
    import speech_recognition as sr
    import pyttsx3

    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False
    print("Voice libraries not installed. Install with: pip install SpeechRecognition pyttsx3")

import ollama
from mcp_hardware import MCPHardwareClient


class VoiceHardwareAssistant:
    """Voice-controlled hardware assistant using Ollama and MCP."""

    def __init__(
            self,
            model: str = "llama2",
            mcp_host: str = "127.0.0.1",
            mcp_port: int = 8888
    ):
        self.model = model
        self.client = MCPHardwareClient(mcp_host, mcp_port)
        self.logger = logging.getLogger("VoiceHardwareAssistant")

        if HAS_VOICE:
            self.recognizer = sr.Recognizer()
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)

        self.wake_word = "assistant"
        self.system_prompt = """You are a voice-controlled hardware assistant. You can control various hardware devices.

Available commands:
1. LED control: "turn on the red light", "blink the green LED", "turn off all lights"
2. Motor control: "start the motor", "set motor speed to 50%", "stop the motor"
3. Sensor reading: "what's the temperature", "check motion sensor", "read humidity"
4. System info: "what's connected", "list available devices", "system status"

Respond with JSON containing the hardware command.
Example: {"command": "control_led", "params": {"device_id": "red_led", "action": "on"}}
"""

    async def connect(self):
        """Connect to MCP server."""
        await self.client.connect()
        self.speak("Hardware assistant connected and ready")

    def speak(self, text: str):
        """Convert text to speech."""
        if HAS_VOICE:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print(f"Assistant: {text}")

    def listen(self, timeout: int = 5) -> str:
        """Listen for voice input."""
        if not HAS_VOICE:
            return input("Your command: ")

        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")

            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't understand that")
                return ""
            except Exception as e:
                self.logger.error(f"Recognition error: {e}")
                return ""

    async def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process voice command through Ollama."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": command}
        ]

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                format="json"
            )

            command_data = json.loads(response['message']['content'])
            self.logger.info(f"Parsed command: {command_data}")

            return await self.execute_hardware_command(command_data)

        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {"error": str(e)}

    async def execute_hardware_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the hardware command."""
        command = command_data.get("command")
        params = command_data.get("params", {})

        try:
            if command == "control_led":
                result = await self.client.control_led(
                    params["device_id"],
                    params["action"],
                    **{k: v for k, v in params.items() if k not in ["device_id", "action"]}
                )
                self.speak(f"LED {params['action']} completed")

            elif command == "read_sensor":
                sensor_type = params.get("type")
                if sensor_type == "temperature":
                    result = await self.client.send_request("sensor.readTemperature", params)
                    temp = result.get("temperature", 0)
                    self.speak(f"Temperature is {temp} degrees")
                elif sensor_type == "motion":
                    result = await self.client.send_request("sensor.readMotion", params)
                    if result.get("motion_detected"):
                        self.speak("Motion detected")
                    else:
                        self.speak("No motion detected")
                else:
                    result = {"error": f"Unknown sensor type: {sensor_type}"}

            elif command == "list_devices":
                result = await self.client.send_request("system.listDevices", {})
                devices = result.get("devices", [])
                self.speak(f"Found {len(devices)} connected devices")

            else:
                result = {"error": f"Unknown command: {command}"}
                self.speak("Sorry, I don't know that command")

            return result

        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self.speak(f"Error executing command: {str(e)}")
            return {"error": str(e)}

    async def run_assistant(self):
        """Run the voice assistant main loop."""
        await self.connect()

        self.speak("Voice assistant ready. Say 'assistant' followed by your command")

        try:
            while True:
                # Listen for wake word
                text = self.listen(timeout=3)

                if self.wake_word in text:
                    self.speak("Yes?")

                    # Listen for command
                    command = self.listen(timeout=10)

                    if command:
                        if "exit" in command or "quit" in command:
                            self.speak("Goodbye!")
                            break

                        # Process command
                        result = await self.process_voice_command(command)

                        if "error" in result:
                            self.speak(f"Error: {result['error']}")
                        else:
                            self.logger.info(f"Command result: {result}")

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            self.speak("Assistant shutting down")
        finally:
            await self.client.disconnect()


async def demo_scenarios():
    """Run demonstration scenarios."""
    assistant = VoiceHardwareAssistant()
    await assistant.connect()

    # Demo scenarios
    scenarios = [
        {
            "announce": "Let me show you what I can do",
            "commands": [
                "Turn on the red LED",
                "Blink the green LED 5 times",
                "Check the temperature sensor",
                "Is there any motion detected?",
                "Turn off all lights"
            ]
        },
        {
            "announce": "Now let's try some automation",
            "commands": [
                "Start monitoring motion sensor",
                "If motion detected, turn on security light",
                "After 30 seconds, turn off security light"
            ]
        }
    ]

    for scenario in scenarios:
        assistant.speak(scenario["announce"])

        for command in scenario["commands"]:
            assistant.speak(f"Executing: {command}")
            result = await assistant.process_voice_command(command)
            await asyncio.sleep(2)

    await assistant.client.disconnect()


async def interactive_mode():
    """Run in interactive mode."""
    assistant = VoiceHardwareAssistant()
    await assistant.run_assistant()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Voice Hardware Assistant")
    parser.add_argument("--mode", choices=["interactive", "demo"],
                        default="interactive", help="Running mode")
    parser.add_argument("--model", default="llama2", help="Ollama model to use")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.mode == "demo":
        asyncio.run(demo_scenarios())
    else:
        asyncio.run(interactive_mode())