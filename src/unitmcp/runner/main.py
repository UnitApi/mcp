#!/usr/bin/env python3
"""
UnitMCP Runner Main Module

This module provides the main functionality for the UnitMCP Runner,
which coordinates server and client setup, LLM integration, and hardware control.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnitMCPRunner:
    """
    Main class for the UnitMCP Runner.
    
    This class coordinates the server and client setup, LLM integration,
    and hardware control based on the provided configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the UnitMCP Runner.
        
        Args:
            config: Configuration dictionary for the runner
        """
        self.config = config
        self.server_setup = None
        self.client_setup = None
        self.llm_interface = None
        self.running = False
        self.logger = logging.getLogger("UnitMCPRunner")
        
    async def initialize(self) -> bool:
        """
        Initialize all components of the runner.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Import components here to avoid circular imports
            from unitmcp.runner.server_setup import ServerSetup
            from unitmcp.runner.client_setup import ClientSetup
            from unitmcp.runner.llm_interface import LLMInterface
            from unitmcp.runner.ollama_interface import OllamaInterface
            
            # Initialize server setup if enabled
            if self.config.get('server', {}).get('enabled', True):
                self.logger.info("Initializing server setup...")
                self.server_setup = ServerSetup(self.config.get('server', {}))
                await self.server_setup.initialize()
                
            # Initialize client setup if enabled
            if self.config.get('client', {}).get('enabled', True):
                self.logger.info("Initializing client setup...")
                self.client_setup = ClientSetup(self.config.get('client', {}))
                await self.client_setup.initialize()
                
            # Initialize LLM interface if enabled
            if self.config.get('llm', {}).get('enabled', True):
                llm_type = self.config.get('llm', {}).get('type', 'ollama')
                self.logger.info(f"Initializing LLM interface ({llm_type})...")
                
                if llm_type == 'ollama':
                    self.llm_interface = OllamaInterface(self.config.get('llm', {}))
                elif llm_type == 'claude':
                    from unitmcp.runner.claude_integration import ClaudeIntegration
                    self.llm_interface = ClaudeIntegration(self.config.get('llm', {}))
                else:
                    self.logger.error(f"Unknown LLM type: {llm_type}")
                    return False
                
                await self.llm_interface.initialize()
                
            self.logger.info("UnitMCP Runner initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing UnitMCP Runner: {e}")
            return False
            
    async def start(self) -> bool:
        """
        Start the UnitMCP Runner.
        
        Returns:
            True if start was successful, False otherwise
        """
        try:
            if not await self.initialize():
                self.logger.error("Failed to initialize UnitMCP Runner")
                return False
                
            self.logger.info("Starting UnitMCP Runner...")
            
            # Start server if initialized
            if self.server_setup:
                await self.server_setup.start()
                
            # Start client if initialized
            if self.client_setup:
                await self.client_setup.start()
                
            # Start LLM interface if initialized
            if self.llm_interface:
                await self.llm_interface.start()
                
            self.running = True
            self.logger.info("UnitMCP Runner started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting UnitMCP Runner: {e}")
            return False
            
    async def stop(self) -> bool:
        """
        Stop the UnitMCP Runner.
        
        Returns:
            True if stop was successful, False otherwise
        """
        try:
            self.logger.info("Stopping UnitMCP Runner...")
            
            # Stop LLM interface if initialized
            if self.llm_interface:
                await self.llm_interface.stop()
                
            # Stop client if initialized
            if self.client_setup:
                await self.client_setup.stop()
                
            # Stop server if initialized
            if self.server_setup:
                await self.server_setup.stop()
                
            self.running = False
            self.logger.info("UnitMCP Runner stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping UnitMCP Runner: {e}")
            return False
            
    async def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a natural language command using the LLM interface.
        
        Args:
            command: Natural language command to process
            
        Returns:
            Dictionary with the result of the command processing
        """
        if not self.llm_interface:
            return {"success": False, "error": "LLM interface not initialized"}
            
        if not self.client_setup:
            return {"success": False, "error": "Client not initialized"}
            
        try:
            # Process command with LLM
            llm_response = await self.llm_interface.generate_response(command)
            
            # Execute the processed command on the hardware
            result = await self.client_setup.execute_command(llm_response)
            
            return {
                "success": True,
                "command": command,
                "llm_response": llm_response,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {"success": False, "error": str(e)}
            
    async def run_interactive(self) -> None:
        """
        Run the UnitMCP Runner in interactive mode.
        
        This method starts an interactive session where the user can
        enter natural language commands to control hardware devices.
        """
        if not await self.start():
            self.logger.error("Failed to start UnitMCP Runner")
            return
            
        self.logger.info("Starting interactive session. Type 'exit' to quit.")
        
        while True:
            try:
                command = input("UnitMCP> ")
                
                if command.lower() in ['exit', 'quit']:
                    break
                    
                if not command.strip():
                    continue
                    
                result = await self.process_command(command)
                
                if result.get('success'):
                    print(f"Result: {result.get('result')}")
                else:
                    print(f"Error: {result.get('error')}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in interactive session: {e}")
                
        await self.stop()
        self.logger.info("Interactive session ended")


async def run_from_config(config_path: str) -> Optional[UnitMCPRunner]:
    """
    Run the UnitMCP Runner from a configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        UnitMCPRunner instance if successful, None otherwise
    """
    try:
        # Simple YAML loader implementation to avoid circular imports
        import yaml
        
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            if not config:
                logger.error(f"Failed to load configuration from {config_path}")
                return None
                
            # Process environment variables in the config
            config = _process_env_vars(config)
                
            # Create and start runner
            runner = UnitMCPRunner(config)
            if not await runner.start():
                logger.error("Failed to start UnitMCP Runner")
                return None
                
            return runner
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error running UnitMCP Runner from config: {e}")
        return None
        
def _process_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process environment variables in the configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Processed configuration dictionary
    """
    import os
    import re
    
    if isinstance(config, dict):
        return {k: _process_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_process_env_vars(v) for v in config]
    elif isinstance(config, str):
        # Replace ${VAR} with environment variable
        pattern = r'\${([^}]+)}'
        matches = re.findall(pattern, config)
        
        if matches:
            result = config
            for match in matches:
                env_value = os.environ.get(match, '')
                result = result.replace(f'${{{match}}}', env_value)
            return result
        
        # Replace $VAR with environment variable
        if config.startswith('$') and config[1:] in os.environ:
            return os.environ[config[1:]]
            
    return config
