#!/usr/bin/env python3
"""
UnitMCP Git Runner Integration

This module integrates the GitRunner with the UnitMCP runner system,
allowing for running applications from Git repositories with UnitMCP functionality.
"""

import os
import sys
import asyncio
import argparse
import logging
import yaml
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

# Import the base runner and git runner
from examples.runner.base_runner import BaseRunner
from examples.runner.git_runner import GitRunner
from examples.runner.runner import UnitMCPAdvancedRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitRunnerIntegration:
    """
    Integration between GitRunner and UnitMCP runner.
    
    This class provides functionality to:
    - Clone Git repositories
    - Detect UnitMCP configuration
    - Run applications with UnitMCP runner
    """
    
    def __init__(
        self,
        git_url: str,
        target_dir: Optional[str] = None,
        branch: Optional[str] = None,
        interactive: bool = True,
        auto_start: bool = True,
        log_level: str = "INFO",
        server_host: Optional[str] = None,
        server_port: Optional[int] = None,
        mode: str = "both",
        simulation: bool = False
    ):
        """
        Initialize the Git Runner Integration.
        
        Parameters
        ----------
        git_url : str
            URL of the Git repository to clone
        target_dir : Optional[str]
            Directory to clone the repository into (default: temporary directory)
        branch : Optional[str]
            Branch to checkout (default: default branch)
        interactive : bool
            Whether to prompt for user input when needed (default: True)
        auto_start : bool
            Whether to automatically start the application after setup (default: True)
        log_level : str
            Logging level (default: INFO)
        server_host : Optional[str]
            Server host (overrides config)
        server_port : Optional[int]
            Server port (overrides config)
        mode : str
            Mode of operation: "server", "client", or "both"
        simulation : bool
            Run in simulation mode (overrides config)
        """
        self.git_url = git_url
        self.branch = branch
        self.interactive = interactive
        self.auto_start = auto_start
        self.server_host = server_host
        self.server_port = server_port
        self.mode = mode
        self.simulation = simulation
        
        # Set up logging
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logging.getLogger().setLevel(numeric_level)
        
        # Set target directory
        if target_dir:
            self.target_dir = os.path.abspath(target_dir)
        else:
            # Create a temporary directory
            self.temp_dir = tempfile.TemporaryDirectory()
            self.target_dir = self.temp_dir.name
        
        # Initialize state variables
        self.git_runner = None
        self.unitmcp_runner = None
        self.config_path = None
        self.env_file = None
    
    def __del__(self):
        """Clean up resources."""
        # Clean up temporary directory if used
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    async def run(self) -> int:
        """
        Run the Git Runner Integration workflow.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Create and run the Git Runner
            self.git_runner = GitRunner(
                git_url=self.git_url,
                target_dir=self.target_dir,
                branch=self.branch,
                interactive=self.interactive,
                auto_start=False,  # We'll handle starting the application ourselves
                log_level=logging.getLevelName(logging.getLogger().level)
            )
            
            # Clone the repository and install dependencies
            if not await self.git_runner.clone_repository():
                return 1
            
            # Detect application type
            self.git_runner.app_type = self.git_runner.detect_app_type()
            if not self.git_runner.app_type:
                logger.error("Could not detect application type")
                return 1
            
            logger.info(f"Detected application type: {self.git_runner.app_type}")
            
            # Load environment variables
            if not await self.git_runner.load_env_vars():
                return 1
            
            # Install dependencies
            if not await self.git_runner.install_dependencies():
                return 1
            
            # Check for UnitMCP configuration
            if not self._detect_unitmcp_config():
                logger.warning("No UnitMCP configuration found. Using standard Git Runner.")
                
                # If no UnitMCP configuration found, use the standard Git Runner
                if self.auto_start:
                    if not await self.git_runner.start_application():
                        return 1
                    
                    # Monitor logs
                    await self.git_runner.monitor_logs()
                
                return 0
            
            # Run with UnitMCP runner
            return await self._run_with_unitmcp()
        
        except Exception as e:
            logger.exception(f"Error running Git Runner Integration: {e}")
            return 1
    
    def _detect_unitmcp_config(self) -> bool:
        """
        Detect UnitMCP configuration in the repository.
        
        Returns
        -------
        bool
            True if UnitMCP configuration found, False otherwise
        """
        # Check for UnitMCP configuration files
        config_files = [
            "unitmcp_config.yaml",
            "unitmcp_config.yml",
            "unitmcp_config.json",
            "configs/unitmcp_config.yaml",
            "configs/unitmcp_config.yml",
            "configs/unitmcp_config.json",
            "configs/yaml/runner/default_runner.yaml",
            "configs/yaml/runner/runner.yaml",
            "config/runner.yaml",
            "config/runner.yml",
            "config/unitmcp.yaml",
            "config/unitmcp.yml"
        ]
        
        for config_file in config_files:
            full_path = os.path.join(self.target_dir, config_file)
            if os.path.exists(full_path):
                self.config_path = full_path
                logger.info(f"Found UnitMCP configuration: {config_file}")
                return True
        
        # Check for .env file with UnitMCP configuration
        env_files = [
            ".env",
            ".env.unitmcp",
            "config/.env",
            "configs/.env"
        ]
        
        for env_file in env_files:
            full_path = os.path.join(self.target_dir, env_file)
            if os.path.exists(full_path):
                # Check if it contains UnitMCP configuration
                with open(full_path, "r") as f:
                    content = f.read()
                    if "SERVER_HOST" in content or "SERVER_PORT" in content or "UNITMCP" in content:
                        self.env_file = full_path
                        logger.info(f"Found UnitMCP environment file: {env_file}")
                        return True
        
        # Check for client.py and server.py files
        client_file = os.path.join(self.target_dir, "client.py")
        server_file = os.path.join(self.target_dir, "server.py")
        
        if os.path.exists(client_file) and os.path.exists(server_file):
            logger.info("Found client.py and server.py files")
            return True
        
        # Check for client and server directories
        client_dir = os.path.join(self.target_dir, "client")
        server_dir = os.path.join(self.target_dir, "server")
        
        if os.path.isdir(client_dir) and os.path.isdir(server_dir):
            logger.info("Found client and server directories")
            return True
        
        return False
    
    async def _run_with_unitmcp(self) -> int:
        """
        Run the application with UnitMCP runner.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Create UnitMCP runner configuration
            if self.config_path:
                # Use existing configuration
                config_path = self.config_path
            else:
                # Create temporary configuration
                config_path = os.path.join(self.target_dir, "unitmcp_config.yaml")
                self._create_unitmcp_config(config_path)
            
            # Create UnitMCP runner
            self.unitmcp_runner = UnitMCPAdvancedRunner(
                config_path=config_path,
                env_file=self.env_file,
                mode=self.mode,
                server_host=self.server_host,
                server_port=self.server_port,
                simulation=self.simulation
            )
            
            # Run the UnitMCP runner
            if self.interactive:
                return await self.unitmcp_runner.run_interactive()
            else:
                return await self.unitmcp_runner.run_async()
        
        except Exception as e:
            logger.exception(f"Error running with UnitMCP: {e}")
            return 1
    
    def _create_unitmcp_config(self, config_path: str) -> None:
        """
        Create a UnitMCP configuration file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file to create
        """
        # Detect client and server files/directories
        client_file = os.path.join(self.target_dir, "client.py")
        server_file = os.path.join(self.target_dir, "server.py")
        client_dir = os.path.join(self.target_dir, "client")
        server_dir = os.path.join(self.target_dir, "server")
        
        # Create configuration
        config = {
            "server": {
                "enabled": True,
                "host": self.server_host or "localhost",
                "port": self.server_port or 8888,
                "simulation": self.simulation
            },
            "client": {
                "enabled": True,
                "server_host": self.server_host or "localhost",
                "server_port": self.server_port or 8888
            }
        }
        
        # Add script paths if found
        if os.path.exists(server_file):
            config["server"]["script_path"] = server_file
        elif os.path.isdir(server_dir):
            # Look for main.py or server.py in server directory
            for file in ["main.py", "server.py", "app.py", "run.py"]:
                if os.path.exists(os.path.join(server_dir, file)):
                    config["server"]["script_path"] = os.path.join(server_dir, file)
                    break
        
        if os.path.exists(client_file):
            config["client"]["script_path"] = client_file
        elif os.path.isdir(client_dir):
            # Look for main.py or client.py in client directory
            for file in ["main.py", "client.py", "app.py", "run.py"]:
                if os.path.exists(os.path.join(client_dir, file)):
                    config["client"]["script_path"] = os.path.join(client_dir, file)
                    break
        
        # Write configuration to file
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        logger.info(f"Created UnitMCP configuration: {config_path}")


class GitRunnerIntegrationCLI:
    """Command-line interface for the Git Runner Integration."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.parser = argparse.ArgumentParser(
            description="UnitMCP Git Runner Integration - Run applications from Git repositories with UnitMCP"
        )
        
        self.parser.add_argument(
            "git_url",
            help="URL of the Git repository to clone"
        )
        
        self.parser.add_argument(
            "--target-dir", "-d",
            help="Directory to clone the repository into (default: temporary directory)"
        )
        
        self.parser.add_argument(
            "--branch", "-b",
            help="Branch to checkout (default: default branch)"
        )
        
        self.parser.add_argument(
            "--non-interactive", "-n",
            action="store_true",
            help="Run in non-interactive mode (don't prompt for input)"
        )
        
        self.parser.add_argument(
            "--no-auto-start", "-s",
            action="store_true",
            help="Don't automatically start the application after setup"
        )
        
        self.parser.add_argument(
            "--log-level", "-l",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Logging level (default: INFO)"
        )
        
        self.parser.add_argument(
            "--server-host",
            help="Server host (overrides config)"
        )
        
        self.parser.add_argument(
            "--server-port",
            type=int,
            help="Server port (overrides config)"
        )
        
        self.parser.add_argument(
            "--mode",
            choices=["server", "client", "both"],
            default="both",
            help="Mode of operation: server, client, or both (default: both)"
        )
        
        self.parser.add_argument(
            "--simulation",
            action="store_true",
            help="Run in simulation mode (overrides config)"
        )
    
    async def run(self) -> int:
        """
        Run the CLI.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        args = self.parser.parse_args()
        
        integration = GitRunnerIntegration(
            git_url=args.git_url,
            target_dir=args.target_dir,
            branch=args.branch,
            interactive=not args.non_interactive,
            auto_start=not args.no_auto_start,
            log_level=args.log_level,
            server_host=args.server_host,
            server_port=args.server_port,
            mode=args.mode,
            simulation=args.simulation
        )
        
        return await integration.run()


async def main() -> int:
    """
    Main entry point.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    cli = GitRunnerIntegrationCLI()
    return await cli.run()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
