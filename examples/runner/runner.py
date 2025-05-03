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

# Import the base runner
from examples.runner.base_runner import BaseRunner

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


class UnitMCPAdvancedRunner(BaseRunner):
    """
    Advanced runner for UnitMCP that extends the base runner functionality.
    
    This class adds UnitMCP-specific features on top of the base runner:
    - Integration with UnitMCPRunner from the UnitMCP package
    - Support for LLM integration
    - Interactive mode
    - Simulation mode
    """
    
    def __init__(self, config_path, env_file=None, mode="both", 
                 server_host=None, server_port=None, simulation=False):
        """
        Initialize the UnitMCP Advanced Runner.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
        env_file : str, optional
            Path to the environment file
        mode : str, optional
            Mode of operation: "server", "client", or "both"
        server_host : str, optional
            Server host (overrides config)
        server_port : int, optional
            Server port (overrides config)
        simulation : bool, optional
            Run in simulation mode (overrides config)
        """
        # Load environment variables if specified
        if env_file:
            env_loader = EnvLoader()
            if not env_loader.load_env_file(env_file):
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
        
        # Load the UnitMCP runner configuration
        self.unitmcp_runner = None
        self.mode = mode
        self.server_host = server_host
        self.server_port = server_port
        self.simulation = simulation
        self.config_path = config_path
        
        # Initialize the base runner with placeholder config paths
        # We'll use the UnitMCP runner for actual functionality
        super().__init__(
            server_config_path=config_path,
            client_config_path=config_path
        )
    
    async def initialize_unitmcp_runner(self):
        """
        Initialize the UnitMCP runner from configuration.
        
        Returns
        -------
        bool
            True if initialization was successful, False otherwise
        """
        try:
            # Run the UnitMCP Runner from the configuration
            self.unitmcp_runner = await run_from_config(self.config_path)
            
            if not self.unitmcp_runner:
                logger.error("Failed to initialize UnitMCP Runner")
                return False
                
            # Override configuration with command-line arguments
            if self.server_host:
                if self.unitmcp_runner.server_setup:
                    self.unitmcp_runner.server_setup.host = self.server_host
                if self.unitmcp_runner.client_setup:
                    self.unitmcp_runner.client_setup.server_host = self.server_host
                    
            if self.server_port:
                if self.unitmcp_runner.server_setup:
                    self.unitmcp_runner.server_setup.port = self.server_port
                if self.unitmcp_runner.client_setup:
                    self.unitmcp_runner.client_setup.server_port = self.server_port
                    
            if self.simulation and self.unitmcp_runner.server_setup:
                self.unitmcp_runner.server_setup.simulation = True
                
            # Apply the mode of operation
            if self.mode != "both":
                if self.mode == "server":
                    if self.unitmcp_runner.client_setup:
                        self.unitmcp_runner.client_setup = None
                elif self.mode == "client":
                    if self.unitmcp_runner.server_setup:
                        self.unitmcp_runner.server_setup = None
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing UnitMCP Runner: {e}")
            return False
    
    async def start_server(self):
        """
        Start the server using the UnitMCP runner.
        
        Returns
        -------
        bool
            True if the server was started successfully, False otherwise
        """
        if not self.unitmcp_runner:
            if not await self.initialize_unitmcp_runner():
                return False
        
        if self.unitmcp_runner.server_setup:
            await self.unitmcp_runner.server_setup.start()
            return True
        
        return False
    
    async def start_client(self):
        """
        Start the client using the UnitMCP runner.
        
        Returns
        -------
        bool
            True if the client was started successfully, False otherwise
        """
        if not self.unitmcp_runner:
            if not await self.initialize_unitmcp_runner():
                return False
        
        if self.unitmcp_runner.client_setup:
            await self.unitmcp_runner.client_setup.start()
            return True
        
        return False
    
    async def stop_processes(self):
        """
        Stop all processes using the UnitMCP runner.
        
        Returns
        -------
        bool
            True if all processes were stopped successfully, False otherwise
        """
        if self.unitmcp_runner:
            await self.unitmcp_runner.stop()
            return True
        
        return False
    
    async def run_interactive(self):
        """
        Run the UnitMCP runner in interactive mode.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        if not self.unitmcp_runner:
            if not await self.initialize_unitmcp_runner():
                return 1
        
        await self.unitmcp_runner.run_interactive()
        return 0
    
    async def run_async(self):
        """
        Run the UnitMCP runner asynchronously.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        try:
            if not self.unitmcp_runner:
                if not await self.initialize_unitmcp_runner():
                    return 1
            
            # Start the UnitMCP runner
            if not await self.unitmcp_runner.start():
                logger.error("Failed to start UnitMCP Runner")
                return 1
                
            logger.info("UnitMCP Runner started. Press Ctrl+C to stop.")
            
            # Keep the runner running until interrupted
            self.running = True
            while self.running:
                await asyncio.sleep(1)
                
            await self.unitmcp_runner.stop()
            return 0
            
        except Exception as e:
            logger.error(f"Error running UnitMCP Runner: {e}")
            if self.unitmcp_runner:
                await self.unitmcp_runner.stop()
            return 1


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
    
    # Create the runner
    try:
        runner = UnitMCPAdvancedRunner(
            config_path=args.config,
            env_file=args.env,
            mode=args.mode,
            server_host=args.server_host,
            server_port=args.server_port,
            simulation=args.simulation
        )
        
        # Run in interactive mode if specified
        if args.interactive:
            return await runner.run_interactive()
        else:
            # Otherwise, just start the runner and keep it running
            return await runner.run_async()
            
    except Exception as e:
        logger.error(f"Error creating UnitMCP Runner: {e}")
        return 1


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
