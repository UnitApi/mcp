#!/usr/bin/env python3
"""
UnitMCP Standalone Runner

A simplified standalone runner that doesn't rely on the UnitMCP package structure.
This avoids import issues and circular dependencies.
"""

import os
import sys
import asyncio
import argparse
import logging
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandaloneRunner:
    """
    Standalone implementation of the UnitMCP Runner.
    
    This class provides a simplified version of the UnitMCP Runner
    that doesn't rely on the UnitMCP package structure.
    """
    
    def __init__(self, config):
        """Initialize the runner with the given configuration."""
        self.config = config
        self.running = False
        self.logger = logging.getLogger("StandaloneRunner")
        
    async def start(self):
        """Start the runner."""
        self.logger.info("Starting UnitMCP Standalone Runner")
        self.running = True
        
        # Print the configuration
        self.logger.info("Configuration:")
        for section, settings in self.config.items():
            if isinstance(settings, dict):
                self.logger.info(f"  {section}:")
                for key, value in settings.items():
                    if not isinstance(value, dict) and not isinstance(value, list):
                        self.logger.info(f"    {key}: {value}")
            else:
                self.logger.info(f"  {section}: {settings}")
                
        return True
        
    async def stop(self):
        """Stop the runner."""
        self.logger.info("Stopping UnitMCP Standalone Runner")
        self.running = False
        return True
        
    async def run_interactive(self):
        """Run the runner in interactive mode."""
        if not self.running:
            await self.start()
            
        self.logger.info("Running in interactive mode. Enter commands or 'exit' to quit.")
        
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\nEnter command: ")
                )
                
                if command.lower() in ['exit', 'quit']:
                    self.logger.info("Exiting interactive mode")
                    break
                    
                self.logger.info(f"Processing command: {command}")
                
                # In a real implementation, we would process the command here
                # For now, just echo it back
                self.logger.info(f"Command received: {command}")
                
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
                
        await self.stop()


def load_config(config_path):
    """Load configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if not config:
            logger.error(f"Failed to load configuration from {config_path}")
            return None
            
        # Process environment variables in the config
        config = process_env_vars(config)
        return config
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None


def process_env_vars(config):
    """Process environment variables in the configuration."""
    import os
    import re
    
    if isinstance(config, dict):
        return {k: process_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [process_env_vars(v) for v in config]
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


def load_env_file(env_file):
    """Load environment variables from a file."""
    try:
        if not os.path.exists(env_file):
            logger.error(f"Environment file not found: {env_file}")
            return False
            
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')
                
        return True
    except Exception as e:
        logger.error(f"Error loading environment file: {e}")
        return False


async def main():
    """Main function for the UnitMCP Standalone Runner."""
    parser = argparse.ArgumentParser(description="UnitMCP Standalone Runner")
    parser.add_argument("--config", type=str, default="configs/yaml/runner/default_runner.yaml",
                       help="Path to the configuration file")
    parser.add_argument("--env", type=str, default=None,
                       help="Path to the environment file")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--command", type=str, default=None,
                       help="Execute a single command and exit")
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Load environment variables if specified
    if args.env:
        if not load_env_file(args.env):
            logger.error(f"Failed to load environment from {args.env}")
            return 1
            
    # Resolve the configuration path
    config_path = args.config
    if not os.path.isabs(config_path):
        # If it's a relative path, try to resolve it relative to the project root
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = os.path.join(project_root, config_path)
        
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return 1
        
    # Load the configuration
    config = load_config(config_path)
    if not config:
        logger.error("Failed to load configuration")
        return 1
        
    # Create and start the runner
    runner = StandaloneRunner(config)
    
    # Start the runner
    if not await runner.start():
        logger.error("Failed to start UnitMCP Standalone Runner")
        return 1
    
    # If a command is specified, execute it and exit
    if args.command:
        logger.info(f"Executing command: {args.command}")
        # In a real implementation, we would process the command here
        logger.info(f"Command received: {args.command}")
        await runner.stop()
        return 0
    
    # Run in interactive mode if specified and we're in a terminal
    if args.interactive and sys.stdin.isatty():
        await runner.run_interactive()
    else:
        # Otherwise, just start the runner and keep it running
        logger.info("UnitMCP Standalone Runner started. Press Ctrl+C to stop.")
        
        try:
            # Keep the runner running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping UnitMCP Standalone Runner...")
            await runner.stop()
            
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("UnitMCP Standalone Runner stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
