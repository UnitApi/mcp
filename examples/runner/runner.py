#!/usr/bin/env python3
"""
UnitMCP Runner

A service that configures and runs both client and server environments
based on YAML configuration, allowing for remote hardware control through
a local Ollama LLM instance.
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)
print(f"Added {project_root} to Python path")

# Try to import directly from the source directory
try:
    from src.unitmcp.runner.main import UnitMCPRunner, run_from_config
    print("Imported from src.unitmcp")
except ImportError:
    # If that fails, try the regular import
    try:
        from unitmcp.runner.main import UnitMCPRunner, run_from_config
        print("Imported from unitmcp")
    except ImportError:
        print("Failed to import UnitMCPRunner. Make sure the module is installed or in the Python path.")
        sys.exit(1)

# Create a simple EnvLoader implementation for this script
class EnvLoader:
    """Simple environment variable loader."""
    
    def load_env_file(self, env_file):
        """Load environment variables from a file."""
        try:
            if not os.path.exists(env_file):
                logging.error(f"Environment file not found: {env_file}")
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
            logging.error(f"Error loading environment file: {e}")
            return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function for the UnitMCP Runner."""
    parser = argparse.ArgumentParser(description="UnitMCP Runner")
    parser.add_argument("--config", type=str, default="configs/yaml/runner/default_runner.yaml",
                       help="Path to the configuration file")
    parser.add_argument("--env", type=str, default=None,
                       help="Path to the environment file")
    parser.add_argument("--mode", type=str, choices=["server", "client", "both"], default="both",
                       help="Mode of operation: server, client, or both")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode")
    parser.add_argument("--server-host", type=str, default=None,
                       help="Server host (overrides config)")
    parser.add_argument("--server-port", type=int, default=None,
                       help="Server port (overrides config)")
    parser.add_argument("--simulation", action="store_true",
                       help="Run in simulation mode (overrides config)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Load environment variables if specified
    if args.env:
        env_loader = EnvLoader()
        if not env_loader.load_env_file(args.env):
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
        
    # Run the UnitMCP Runner from the configuration
    runner = await run_from_config(config_path)
    
    if not runner:
        logger.error("Failed to initialize UnitMCP Runner")
        return 1
        
    # Override configuration with command-line arguments
    if args.server_host:
        if runner.server_setup:
            runner.server_setup.host = args.server_host
        if runner.client_setup:
            runner.client_setup.server_host = args.server_host
            
    if args.server_port:
        if runner.server_setup:
            runner.server_setup.port = args.server_port
        if runner.client_setup:
            runner.client_setup.server_port = args.server_port
            
    if args.simulation and runner.server_setup:
        runner.server_setup.simulation = True
        
    # Apply the mode of operation
    if args.mode != "both":
        if args.mode == "server":
            if runner.client_setup:
                runner.client_setup = None
        elif args.mode == "client":
            if runner.server_setup:
                runner.server_setup = None
                
    # Run in interactive mode if specified
    if args.interactive:
        await runner.run_interactive()
    else:
        # Otherwise, just start the runner and keep it running
        if not await runner.start():
            logger.error("Failed to start UnitMCP Runner")
            return 1
            
        logger.info("UnitMCP Runner started. Press Ctrl+C to stop.")
        
        try:
            # Keep the runner running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping UnitMCP Runner...")
            await runner.stop()
            
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("UnitMCP Runner stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
