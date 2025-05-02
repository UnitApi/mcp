#!/usr/bin/env python3
"""
LLM Hardware Client Example

This example demonstrates how to use an LLM to interact with the MCP server
for hardware control through natural language.
"""

import asyncio
import logging
import os
import json
import argparse
import httpx
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMClient:
    """Simple LLM client for natural language hardware control."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key for the LLM service
            model: LLM model to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a response from the LLM.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            The LLM's response as a string
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Error getting LLM response: {e}")
                return f"Error: {str(e)}"


class MCPHardwareController:
    """Controller for interacting with MCP hardware server."""
    
    def __init__(self, server_command: str, server_args: List[str] = None):
        """
        Initialize the MCP hardware controller.
        
        Args:
            server_command: Command to start the MCP server
            server_args: Arguments for the server command
        """
        self.server_command = server_command
        self.server_args = server_args or []
        self.session: Optional[ClientSession] = None
        self.tools_info = []
    
    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=os.environ
        )
        
        try:
            read_stream, write_stream = await stdio_client(server_params)
            self.session = ClientSession(read_stream, write_stream)
            await self.session.initialize()
            logger.info("Connected to MCP server")
            
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
            logger.info("Disconnected from MCP server")
    
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


async def process_llm_response(llm_response: str, controller: MCPHardwareController) -> str:
    """
    Process the LLM response and execute tools if needed.
    
    Args:
        llm_response: The response from the LLM
        controller: The MCP hardware controller
        
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


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="LLM Hardware Client Example")
    parser.add_argument(
        "--server-command",
        default="python",
        help="Command to start the MCP server (default: python)"
    )
    parser.add_argument(
        "--server-args",
        nargs="+",
        default=["rpi_control/examples/llm_hardware_control.py"],
        help="Arguments for the server command (default: rpi_control/examples/llm_hardware_control.py)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="API key for the LLM service (default: from OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="LLM model to use (default: gpt-3.5-turbo)"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        logger.error("No API key provided. Set OPENAI_API_KEY environment variable or use --api-key")
        return
    
    # Create MCP hardware controller
    controller = MCPHardwareController(args.server_command, args.server_args)
    
    try:
        # Connect to MCP server
        await controller.connect()
        
        # Create LLM client
        llm_client = LLMClient(args.api_key, args.model)
        
        # Get tools description
        tools_description = controller.get_tools_description()
        
        # Create system message with tools description
        system_message = (
            "You are a helpful assistant that controls hardware devices through an MCP server. "
            "You have access to the following tools:\n\n"
            f"{tools_description}\n\n"
            "When you need to control hardware, respond with a JSON object in this format:\n"
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
        
        print("\nHardware Control Assistant\n")
        print("Type 'exit' or 'quit' to end the conversation.")
        print("Type your commands in natural language to control hardware.\n")
        
        while True:
            # Get user input
            user_input = input("You: ")
            
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get LLM response
            print("Assistant: ", end="", flush=True)
            llm_response = await llm_client.get_response(messages)
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
                final_response = await llm_client.get_response(messages)
                print(final_response)
                
                # Add final response
                messages.append({"role": "assistant", "content": final_response})
            else:
                # Add assistant message
                messages.append({"role": "assistant", "content": llm_response})
    
    except Exception as e:
        logger.error(f"Error: {e}")
    
    finally:
        # Disconnect from MCP server
        await controller.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
