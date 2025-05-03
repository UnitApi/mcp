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

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

# Import the base runner
from examples.runner.base_runner import BaseRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandaloneRunner(BaseRunner):
    """
    Standalone implementation of the UnitMCP Runner.
    
    This class provides a simplified version of the UnitMCP Runner
    that doesn't rely on the UnitMCP package structure.
    """
    
    def __init__(self, config_path, env_file=None):
        """
        Initialize the standalone runner.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
        env_file : str, optional
            Path to the environment file
        """
        # Load environment variables if specified
        if env_file:
            if not load_env_file(env_file):
                logger.error(f"Failed to load environment from {env_file}")
                raise RuntimeError(f"Failed to load environment from {env_file}")
        
        # Resolve the configuration path
        if not os.path.isabs(config_path):
            # If it's a relative path, try to resolve it relative to the project root
            project_root = Path(__file__).resolve().parent.parent.parent
            config_path = os.path.join(project_root, config_path)
            
        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load the configuration
        self.config = load_config(config_path)
        if not self.config:
            logger.error(f"Failed to load configuration from {config_path}")
            raise ValueError(f"Failed to load configuration from {config_path}")
        
        # Extract server and client configurations
        server_config = self.config.get('server', {})
        client_config = self.config.get('client', {})
        
        # Create temporary config files for server and client
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        
        server_config_path = os.path.join(self.temp_dir.name, 'server.yaml')
        with open(server_config_path, 'w') as f:
            yaml.dump(server_config, f)
        
        client_config_path = os.path.join(self.temp_dir.name, 'client.yaml')
        with open(client_config_path, 'w') as f:
            yaml.dump(client_config, f)
        
        # Initialize the base runner
        super().__init__(
            server_config_path=server_config_path,
            client_config_path=client_config_path
        )
    
    def __del__(self):
        """Clean up temporary files."""
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    async def run_interactive(self):
        """
        Run the runner in interactive mode.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        if not self.running:
            if not self.start_server() or not self.start_client():
                return 1
            self.running = True
            
        logger.info("Running in interactive mode. Enter commands or 'exit' to quit.")
        
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\nEnter command: ")
                )
                
                if command.lower() in ['exit', 'quit']:
                    logger.info("Exiting interactive mode")
                    break
                    
                logger.info(f"Processing command: {command}")
                
                # In a real implementation, we would process the command here
                # For now, just echo it back
                logger.info(f"Command received: {command}")
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
        self.stop_processes()
        return 0
    
    async def run_command(self, command):
        """
        Run a single command.
        
        Parameters
        ----------
        command : str
            Command to run
            
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        if not self.running:
            if not self.start_server() or not self.start_client():
                return 1
            self.running = True
            
        try:
            logger.info(f"Processing command: {command}")
            
            # In a real implementation, we would process the command here
            # For now, just echo it back
            logger.info(f"Command received: {command}")
            
            self.stop_processes()
            return 0
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.stop_processes()
            return 1


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
    
    try:
        # Create the runner
        runner = StandaloneRunner(
            config_path=args.config,
            env_file=args.env
        )
        
        # Run in interactive mode if specified
        if args.interactive:
            return await runner.run_interactive()
        elif args.command:
            # Run a single command if specified
            return await runner.run_command(args.command)
        else:
            # Otherwise, just run the example
            return runner.run()
            
    except Exception as e:
        logger.error(f"Error creating StandaloneRunner: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("StandaloneRunner stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
