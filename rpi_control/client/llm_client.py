#!/usr/bin/env python3
"""
LLM Hardware Client for Raspberry Pi Simulation

This script creates a client that connects to the Ollama LLM and the Raspberry Pi simulator
to enable natural language control of simulated Raspberry Pi hardware devices.
"""

import asyncio
import logging
import os
import json
import sys
from typing import Dict, Any, List, Optional

import httpx
import unitmcp
from unitmcp import ClientSession, StdioServerParameters
from unitmcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LLMRaspberryPiClient")

# Get environment variables
RPI_HOST = os.getenv('RPI_HOST', 'rpi-simulator')
RPI_PORT = int(os.getenv('RPI_PORT', '8080'))
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'llm-model')
OLLAMA_PORT = int(os.getenv('OLLAMA_PORT', '11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')


class OllamaClient:
    """Client for interacting with Ollama LLM."""
    
    def __init__(self, host: str = OLLAMA_HOST, port: int = OLLAMA_PORT, model: str = OLLAMA_MODEL):
        """
        Initialize the Ollama client.
        
        Args:
            host: Ollama server hostname
            port: Ollama server port
            model: LLM model to use
        """
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}/api"
        self.headers = {"Content-Type": "application/json"}
    
    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a response from the Ollama LLM.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            The LLM's response as a string
        """
        # Convert messages to Ollama format
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
            elif role == "user":
                if prompt:
                    prompt += f"{content} [/INST]"
                else:
                    prompt += f"<s>[INST] {content} [/INST]"
            elif role == "assistant":
                prompt += f" {content} </s><s>[INST] "
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/generate",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result["response"]
            except Exception as e:
                logger.error(f"Error getting Ollama response: {e}")
                return f"Error: {str(e)}"
    
    async def list_models(self) -> List[str]:
        """
        List available models on the Ollama server.
        
        Returns:
            List of available model names
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tags",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return [model["name"] for model in result["models"]]
            except Exception as e:
                logger.error(f"Error listing Ollama models: {e}")
                return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "name": model_name
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pull",
                    headers=self.headers,
                    json=payload,
                    timeout=600.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Error pulling Ollama model: {e}")
                return False


class MCPRaspberryPiController:
    """Controller for interacting with MCP Raspberry Pi simulator."""
    
    def __init__(self, host: str = RPI_HOST, port: int = RPI_PORT):
        """
        Initialize the MCP Raspberry Pi controller.
        
        Args:
            host: Raspberry Pi simulator hostname
            port: Raspberry Pi simulator port
        """
        self.host = host
        self.port = port
        self.session: Optional[unitmcp.ClientSession] = None
        self.tools_info = []
    
    async def connect(self):
        """Connect to the MCP server."""
        # Create a simple server command that connects to the Raspberry Pi simulator
        server_command = "python"
        server_args = ["-c", f"""
import asyncio
import sys
import json

async def main():
    reader, writer = await asyncio.open_connection('{self.host}', {self.port})
    
    # Forward stdin to server
    async def forward_stdin():
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            writer.write(line.encode())
            await writer.drain()
    
    # Forward server responses to stdout
    async def forward_responses():
        while True:
            data = await reader.readline()
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
    
    # Run both tasks
    stdin_task = asyncio.create_task(forward_stdin())
    response_task = asyncio.create_task(forward_responses())
    
    # Wait for either task to complete
    await asyncio.gather(stdin_task, response_task, return_exceptions=True)
    
    writer.close()
    await writer.wait_closed()

asyncio.run(main())
"""]
        
        server_params = unitmcp.StdioServerParameters(
            command=server_command,
            args=server_args,
            env=os.environ
        )
        
        try:
            read_stream, write_stream = await unitmcp.stdio_client(server_params)
            self.session = unitmcp.ClientSession(read_stream, write_stream)
            await self.session.initialize()
            logger.info(f"Connected to MCP server at {self.host}:{self.port}")
            
            # Get available tools
            tools_response = await self.session.list_tools()
            self.tools_info = []
            
            for item in tools_response:
                if isinstance(item, tuple) and item[0] == "tools":
                    for tool in item[1]:
                        self.tools_info.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        })
            
            logger.info(f"Found {len(self.tools_info)} tools")
            
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            logger.info(f"Disconnected from MCP server at {self.host}:{self.port}")
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            The result of the tool execution
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            logger.info(f"Executing tool: {tool_name}")
            logger.info(f"Arguments: {arguments}")
            
            result = await self.session.call_tool(tool_name, arguments)
            logger.info(f"Result: {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            raise
    
    def get_tools_description(self) -> str:
        """
        Get a description of available tools.
        
        Returns:
            A string describing the available tools
        """
        if not self.tools_info:
            return "No tools available"
        
        descriptions = []
        
        for tool in self.tools_info:
            tool_desc = f"Tool: {tool['name']}\nDescription: {tool['description']}\nArguments:"
            
            if "properties" in tool["input_schema"]:
                for arg_name, arg_info in tool["input_schema"]["properties"].items():
                    arg_desc = f"  - {arg_name}: {arg_info.get('description', 'No description')}"
                    if "type" in arg_info:
                        arg_desc += f" (type: {arg_info['type']})"
                    if arg_name in tool["input_schema"].get("required", []):
                        arg_desc += " (required)"
                    tool_desc += f"\n{arg_desc}"
            
            descriptions.append(tool_desc)
        
        return "\n\n".join(descriptions)


async def process_llm_response(llm_response: str, controller: MCPRaspberryPiController) -> str:
    """
    Process the LLM response and execute tools if needed.
    
    Args:
        llm_response: The response from the LLM
        controller: The MCP Raspberry Pi controller
        
    Returns:
        The result of processing the response
    """
    # Try to parse the response as JSON
    try:
        # Check if the response contains a JSON object
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            tool_call = json.loads(json_str)
        else:
            # Try to parse the entire response as JSON
            tool_call = json.loads(llm_response)
        
        # Check if it's a valid tool call
        if "tool" in tool_call and "arguments" in tool_call:
            tool_name = tool_call["tool"]
            arguments = tool_call["arguments"]
            
            # Execute the tool
            result = await controller.execute_tool(tool_name, arguments)
            return f"Tool execution result: {result}"
        
        return "Invalid tool call format in LLM response"
    
    except json.JSONDecodeError:
        # Not a JSON response, treat as a regular message
        return llm_response


async def ensure_model_available(client: OllamaClient, model_name: str) -> bool:
    """
    Ensure the specified model is available on the Ollama server.
    
    Args:
        client: Ollama client
        model_name: Name of the model to check
        
    Returns:
        True if the model is available, False otherwise
    """
    # List available models
    available_models = await client.list_models()
    logger.info(f"Available models: {available_models}")
    
    if model_name in available_models:
        logger.info(f"Model {model_name} is already available")
        return True
    
    # Pull the model if not available
    logger.info(f"Model {model_name} not found, pulling...")
    success = await client.pull_model(model_name)
    
    if success:
        logger.info(f"Successfully pulled model {model_name}")
        return True
    else:
        logger.error(f"Failed to pull model {model_name}")
        return False


async def main():
    """Main function."""
    try:
        # Create Ollama client
        ollama_client = OllamaClient(OLLAMA_HOST, OLLAMA_PORT, OLLAMA_MODEL)
        
        # Ensure model is available
        model_available = await ensure_model_available(ollama_client, OLLAMA_MODEL)
        if not model_available:
            logger.error(f"Model {OLLAMA_MODEL} is not available")
            sys.exit(1)
        
        # Create MCP Raspberry Pi controller
        controller = MCPRaspberryPiController(RPI_HOST, RPI_PORT)
        
        try:
            # Connect to MCP server
            await controller.connect()
            
            # Get tools description
            tools_description = controller.get_tools_description()
            
            # Create system message with tools description
            system_message = (
                "You are a helpful assistant that controls a Raspberry Pi through an MCP server. "
                "You have access to the following tools to control the Raspberry Pi hardware:\n\n"
                f"{tools_description}\n\n"
                "When you need to control the Raspberry Pi hardware, respond with a JSON object in this format:\n"
                "```json\n"
                "{\n"
                '  "tool": "tool_name",\n'
                '  "arguments": {\n'
                '    "arg1": "value1",\n'
                '    "arg2": "value2"\n'
                "  }\n"
                "}\n"
                "```\n\n"
                "If you don't need to control hardware, respond conversationally. "
                "Always be helpful, clear, and concise."
            )
            
            # Start conversation
            messages = [{"role": "system", "content": system_message}]
            
            print("\nRaspberry Pi Control Assistant\n")
            print("Type 'exit' or 'quit' to end the conversation.")
            print("Type your commands in natural language to control the Raspberry Pi.\n")
            
            while True:
                # Get user input
                user_input = input("You: ")
                
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                # Add user message
                messages.append({"role": "user", "content": user_input})
                
                # Get LLM response
                print("Assistant: ", end="", flush=True)
                llm_response = await ollama_client.get_response(messages)
                print(llm_response)
                
                # Process LLM response
                result = await process_llm_response(llm_response, controller)
                
                if result != llm_response:
                    # Add assistant message
                    messages.append({"role": "assistant", "content": llm_response})
                    
                    # Add system message with tool result
                    messages.append({"role": "system", "content": result})
                    
                    # Get final response
                    print("Assistant: ", end="", flush=True)
                    final_response = await ollama_client.get_response(messages)
                    print(final_response)
                    
                    # Add final response
                    messages.append({"role": "assistant", "content": final_response})
                else:
                    # Add assistant message
                    messages.append({"role": "assistant", "content": llm_response})
        
        except ConnectionRefusedError as e:
            print(f"Could not connect to MCP server: {e}")
        
        finally:
            # Disconnect from MCP server
            await controller.disconnect()
    
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
