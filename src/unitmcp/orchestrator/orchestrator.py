"""Main Orchestrator module for UnitMCP."""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from ..utils.logger import setup_logging as setup_logger
from ..client.client import MCPHardwareClient
from ..hardware.gpio import GPIOController

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Orchestrator for managing UnitMCP examples and runners.
    
    This class provides functionality to:
    - Discover available examples
    - Run examples with different configurations
    - Monitor running examples
    - Connect to remote servers
    - Manage simulation vs. real hardware modes
    """
    
    def __init__(self, examples_dir: Optional[str] = None, config_file: Optional[str] = None, quiet: bool = False):
        """
        Initialize the Orchestrator.
        
        Args:
            examples_dir: Path to the examples directory. If None, uses default.
            config_file: Path to the configuration file. If None, uses default.
            quiet: If True, minimize log output and suppress non-essential messages
        """
        self.quiet = quiet
        self.examples_dir = examples_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "examples")
        
        self.config_file = config_file or os.path.join(os.path.expanduser("~"), ".unitmcp", "orchestrator.json")
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize example and server registries
        self.examples = {}
        self.servers = {}
        self.active_runners = {}
        self.current_server = None
        self.recent_servers = []
        
        # Initialize GPIO controller
        self.gpio_controller = GPIOController()
        
        # Discover available examples
        self._discover_examples()
        
        if not self.quiet:
            logger.info(f"Orchestrator initialized with {len(self.examples)} examples")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                if not self.quiet:
                    logger.warning(f"Failed to load config file: {e}")
        
        # Default configuration
        default_config = {
            "default_simulation": True,
            "default_host": "localhost",
            "default_port": 8080,
            "ssh_config": {
                "default_username": "pi",
                "key_path": "~/.ssh/id_rsa",
                "known_hosts_path": "~/.ssh/known_hosts"
            },
            "ssl_config": {
                "enable_ssl": False,
                "cert_path": "./certs/server.crt",
                "key_path": "./certs/server.key",
                "generate_cert": True
            },
            "recent_examples": [],
            "favorite_examples": [],
            "recent_servers": []
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            if not self.quiet:
                logger.warning(f"Failed to save config file: {e}")
    
    def _discover_examples(self) -> None:
        """Discover available examples in the examples directory."""
        self.examples = {}
        
        if not os.path.exists(self.examples_dir):
            if not self.quiet:
                logger.warning(f"Examples directory not found: {self.examples_dir}")
            return
        
        # Get all directories in examples directory
        for item in os.listdir(self.examples_dir):
            item_path = os.path.join(self.examples_dir, item)
            
            # Skip non-directories and special directories
            if not os.path.isdir(item_path) or item.startswith('.') or item.startswith('__'):
                continue
                
            # Check if directory contains a runner.py file or server.py file
            runner_path = os.path.join(item_path, "runner.py")
            server_path = os.path.join(item_path, "server.py")
            
            if os.path.exists(runner_path) or os.path.exists(server_path):
                # Read README.md for description if available
                readme_path = os.path.join(item_path, "README.md")
                description = ""
                
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, 'r') as f:
                            # Extract first paragraph from README
                            lines = []
                            for line in f:
                                if line.strip():
                                    lines.append(line.strip())
                                elif lines:  # Empty line after content
                                    break
                            
                            description = " ".join(lines)
                    except Exception as e:
                        if not self.quiet:
                            logger.warning(f"Failed to read README for {item}: {e}")
                
                # Add example to registry
                self.examples[item] = {
                    "name": item,
                    "path": item_path,
                    "description": description,
                    "has_runner": os.path.exists(runner_path),
                    "has_server": os.path.exists(server_path),
                    "env_file": os.path.join(item_path, ".env") if os.path.exists(os.path.join(item_path, ".env")) else None,
                    "env_example": os.path.join(item_path, ".env.example") if os.path.exists(os.path.join(item_path, ".env.example")) else None
                }
    
    def get_examples(self) -> Dict[str, Dict[str, Any]]:
        """Get all available examples."""
        return self.examples
    
    def get_example(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific example by name."""
        return self.examples.get(name)
    
    def run_example(self, name: str, simulation: bool = None, host: str = None, 
                   port: int = None, ssh_username: str = None, ssh_key_path: str = None,
                   ssl_enabled: bool = None, **kwargs) -> Dict[str, Any]:
        """
        Run an example with the specified configuration.
        
        Args:
            name: Name of the example to run
            simulation: Whether to run in simulation mode
            host: Host to connect to for remote execution
            port: Port to use for connection
            ssh_username: Username for SSH connection
            ssh_key_path: Path to SSH key file
            ssl_enabled: Whether to enable SSL
            **kwargs: Additional arguments to pass to the runner
            
        Returns:
            Dictionary with information about the running example
        """
        example = self.get_example(name)
        if not example:
            raise ValueError(f"Example '{name}' not found")
        
        # Use provided values or defaults from config
        simulation = simulation if simulation is not None else self.config.get("default_simulation", True)
        host = host or self.config.get("default_host", "localhost")
        port = port or self.config.get("default_port", 8080)
        ssh_username = ssh_username or self.config.get("ssh_config", {}).get("default_username", "pi")
        ssh_key_path = ssh_key_path or self.config.get("ssh_config", {}).get("key_path", "~/.ssh/id_rsa")
        ssl_enabled = ssl_enabled if ssl_enabled is not None else self.config.get("ssl_config", {}).get("enable_ssl", False)
        
        # Prepare environment variables
        env = os.environ.copy()
        env["SIMULATION"] = "1" if simulation else "0"
        env["SERVER_HOST"] = host
        env["SERVER_PORT"] = str(port)
        env["RPI_USERNAME"] = ssh_username
        env["SSH_KEY_PATH"] = os.path.expanduser(ssh_key_path)
        env["ENABLE_SSL"] = "true" if ssl_enabled else "false"
        
        # Add example to recent list
        if name in self.config.get("recent_examples", []):
            self.config["recent_examples"].remove(name)
        self.config["recent_examples"].insert(0, name)
        self.config["recent_examples"] = self.config["recent_examples"][:10]  # Keep only 10 most recent
        self._save_config()
        
        # Create a unique ID for this runner
        import uuid
        runner_id = str(uuid.uuid4())
        
        # Store information about the running example
        runner_info = {
            "id": runner_id,
            "example": name,
            "path": example["path"],
            "simulation": simulation,
            "host": host,
            "port": port,
            "ssh_username": ssh_username,
            "ssh_key_path": ssh_key_path,
            "ssl_enabled": ssl_enabled,
            "status": "starting",
            "pid": None,
            "start_time": None,
            "env": env
        }
        
        self.active_runners[runner_id] = runner_info
        
        # Start the runner in a separate process
        import subprocess
        import time
        
        start_time = time.time()
        
        if example["has_runner"]:
            runner_path = os.path.join(example["path"], "runner.py")
            cmd = [sys.executable, runner_path]
            
            # Add any additional arguments
            for key, value in kwargs.items():
                if key.startswith("arg_"):
                    arg_name = key[4:]  # Remove "arg_" prefix
                    cmd.extend([f"--{arg_name}", str(value)])
            
            if not self.quiet:
                logger.info(f"Starting runner for example '{name}': {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                runner_info["pid"] = process.pid
                runner_info["start_time"] = start_time
                runner_info["status"] = "running"
                runner_info["process"] = process
                
                # Add server to recent list if not in simulation mode
                if not simulation:
                    server_info = f"{host}:{port}"
                    if server_info in self.config.get("recent_servers", []):
                        self.config["recent_servers"].remove(server_info)
                    self.config["recent_servers"].insert(0, server_info)
                    self.config["recent_servers"] = self.config["recent_servers"][:10]  # Keep only 10 most recent
                    self._save_config()
                
                return runner_info
            except Exception as e:
                if not self.quiet:
                    logger.error(f"Failed to start runner for example '{name}': {e}")
                runner_info["status"] = "failed"
                runner_info["error"] = str(e)
                return runner_info
        elif example["has_server"]:
            server_path = os.path.join(example["path"], "server.py")
            cmd = [sys.executable, server_path]
            
            # Add any additional arguments
            for key, value in kwargs.items():
                if key.startswith("arg_"):
                    arg_name = key[4:]  # Remove "arg_" prefix
                    cmd.extend([f"--{arg_name}", str(value)])
            
            if not self.quiet:
                logger.info(f"Starting server for example '{name}': {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                runner_info["pid"] = process.pid
                runner_info["start_time"] = start_time
                runner_info["status"] = "running"
                runner_info["process"] = process
                
                # Add server to recent list
                server_info = f"{host}:{port}"
                if server_info in self.config.get("recent_servers", []):
                    self.config["recent_servers"].remove(server_info)
                self.config["recent_servers"].insert(0, server_info)
                self.config["recent_servers"] = self.config["recent_servers"][:10]  # Keep only 10 most recent
                self._save_config()
                
                return runner_info
            except Exception as e:
                if not self.quiet:
                    logger.error(f"Failed to start server for example '{name}': {e}")
                runner_info["status"] = "failed"
                runner_info["error"] = str(e)
                return runner_info
        else:
            runner_info["status"] = "failed"
            runner_info["error"] = "Example has no runner.py or server.py"
            return runner_info
    
    def stop_runner(self, runner_id: str) -> bool:
        """Stop a running example."""
        if runner_id not in self.active_runners:
            if not self.quiet:
                logger.warning(f"Runner '{runner_id}' not found")
            return False
        
        runner_info = self.active_runners[runner_id]
        if runner_info["status"] != "running":
            if not self.quiet:
                logger.warning(f"Runner '{runner_id}' is not running")
            return False
        
        try:
            process = runner_info.get("process")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            runner_info["status"] = "stopped"
            return True
        except Exception as e:
            if not self.quiet:
                logger.error(f"Failed to stop runner '{runner_id}': {e}")
            return False
    
    def get_runner_status(self, runner_id: str) -> Dict[str, Any]:
        """Get status of a running example."""
        if runner_id not in self.active_runners:
            raise ValueError(f"Runner '{runner_id}' not found")
        
        runner_info = self.active_runners[runner_id]
        process = runner_info.get("process")
        
        if process:
            # Check if process is still running
            if process.poll() is not None:
                runner_info["status"] = "finished" if process.returncode == 0 else "failed"
                runner_info["return_code"] = process.returncode
            
            # Get output
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                runner_info["stdout"] = stdout.decode() if stdout else ""
                runner_info["stderr"] = stderr.decode() if stderr else ""
            except subprocess.TimeoutExpired:
                # Process is still running, get output so far
                stdout = process.stdout.read() if process.stdout else b""
                stderr = process.stderr.read() if process.stderr else b""
                runner_info["stdout"] = stdout.decode() if stdout else ""
                runner_info["stderr"] = stderr.decode() if stderr else ""
        
        return runner_info
    
    def get_active_runners(self) -> Dict[str, Dict[str, Any]]:
        """Get all active runners."""
        return self.active_runners
    
    def connect_to_server(self, host: str, port: int, ssl_enabled: bool = False, retry_count: int = 3, timeout: float = 2.0, use_discovery: bool = False) -> Dict[str, Any]:
        """
        Connect to an MCP server.
        
        Args:
            host (str): Server hostname or IP address
            port (int): Server port
            ssl_enabled (bool): Whether to use SSL for the connection
            retry_count (int): Number of connection attempts to make
            timeout (float): Connection timeout in seconds
            use_discovery (bool): Whether to use port discovery if connection fails
            
        Returns:
            dict: Connection information
            
        Raises:
            ConnectionError: If connection fails
        """
        # If already connected to a server, disconnect first
        if self.current_server and self.current_server.get("client"):
            try:
                client = self.current_server.get("client")
                if client and hasattr(client, "disconnect"):
                    asyncio.run(client.disconnect())
                logger.info(f"Disconnected from previous server.")
            except Exception as e:
                logger.warning(f"Could not properly disconnect from previous server: {e}")
        
        # Create a new client
        from ..client.client import MCPHardwareClient
        client = MCPHardwareClient(host=host, port=port)
        
        # Try to connect with retry logic
        try:
            if use_discovery:
                # Use the discovery feature to find the correct port
                success = asyncio.run(client.connect_with_discovery(max_retries=retry_count, retry_delay=timeout))
            else:
                # Use regular retry logic
                success = asyncio.run(client.connect_with_retry(max_retries=retry_count, retry_delay=timeout))
                
            if success:
                # Connection successful
                self.current_server = {
                    "host": host,
                    "port": client.port,  # Use the client's port which might have been updated during discovery
                    "client": client,
                    "status": "connected",
                    "connected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                
                # Add to recent servers list if not already there
                server_key = f"{host}:{client.port}"
                if server_key not in [f"{s['host']}:{s['port']}" for s in self.recent_servers]:
                    self.recent_servers.insert(0, {
                        "host": host,
                        "port": client.port,
                        "last_connected": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    # Keep only the most recent N servers
                    self.recent_servers = self.recent_servers[:10]
                else:
                    # Update the last_connected time for the existing server
                    for server in self.recent_servers:
                        if f"{server['host']}:{server['port']}" == server_key:
                            server["last_connected"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            break
                
                return self.current_server
            else:
                raise ConnectionError("Could not establish a stable connection.")
                
        except Exception as e:
            # Clean up failed connection
            if client and hasattr(client, "disconnect"):
                try:
                    asyncio.run(client.disconnect())
                except:
                    pass
            
            # Reset current server
            self.current_server = None
            
            # Re-raise the exception
            raise
    
    async def handle_gpio_command(self, command: str, args: list) -> Dict[str, Any]:
        """
        Handle a GPIO command.
        
        Args:
            command: The GPIO command (setup, write, read)
            args: Command arguments
            
        Returns:
            Result of the operation
        """
        return await self.gpio_controller.handle_command(command, args)
    
    def get_recent_examples(self) -> List[str]:
        """Get list of recently used examples."""
        return self.config.get("recent_examples", [])
    
    def get_favorite_examples(self) -> List[str]:
        """Get list of favorite examples."""
        return self.config.get("favorite_examples", [])
    
    def add_favorite_example(self, name: str) -> None:
        """Add an example to favorites."""
        if name not in self.examples:
            raise ValueError(f"Example '{name}' not found")
        
        if name not in self.config.get("favorite_examples", []):
            if "favorite_examples" not in self.config:
                self.config["favorite_examples"] = []
            self.config["favorite_examples"].append(name)
            self._save_config()
    
    def remove_favorite_example(self, name: str) -> None:
        """Remove an example from favorites."""
        if name in self.config.get("favorite_examples", []):
            self.config["favorite_examples"].remove(name)
            self._save_config()
    
    def get_recent_servers(self) -> List[str]:
        """Get list of recently connected servers."""
        return self.recent_servers
    
    def create_env_file(self, example_name: str, simulation: bool = None, 
                       host: str = None, port: int = None, 
                       ssh_username: str = None, ssh_key_path: str = None,
                       ssl_enabled: bool = None) -> Optional[str]:
        """
        Create or update .env file for an example.
        
        Args:
            example_name: Name of the example
            simulation: Whether to run in simulation mode
            host: Host to connect to for remote execution
            port: Port to use for connection
            ssh_username: Username for SSH connection
            ssh_key_path: Path to SSH key file
            ssl_enabled: Whether to enable SSL
            
        Returns:
            Path to the created .env file or None if failed
        """
        example = self.get_example(example_name)
        if not example:
            raise ValueError(f"Example '{example_name}' not found")
        
        # Use provided values or defaults from config
        simulation = simulation if simulation is not None else self.config.get("default_simulation", True)
        host = host or self.config.get("default_host", "localhost")
        port = port or self.config.get("default_port", 8080)
        ssh_username = ssh_username or self.config.get("ssh_config", {}).get("default_username", "pi")
        ssh_key_path = ssh_key_path or self.config.get("ssh_config", {}).get("key_path", "~/.ssh/id_rsa")
        ssl_enabled = ssl_enabled if ssl_enabled is not None else self.config.get("ssl_config", {}).get("enable_ssl", False)
        
        # Start with example's .env.example if available
        env_content = {}
        if example["env_example"]:
            try:
                with open(example["env_example"], 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_content[key.strip()] = value.strip()
            except Exception as e:
                if not self.quiet:
                    logger.warning(f"Failed to read .env.example for {example_name}: {e}")
        
        # Update with our values
        env_content["SIMULATION"] = "1" if simulation else "0"
        env_content["SERVER_HOST"] = host
        env_content["SERVER_PORT"] = str(port)
        env_content["RPI_USERNAME"] = ssh_username
        env_content["SSH_KEY_PATH"] = os.path.expanduser(ssh_key_path)
        env_content["ENABLE_SSL"] = "true" if ssl_enabled else "false"
        
        # Write to .env file
        env_file = os.path.join(example["path"], ".env")
        try:
            with open(env_file, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            return env_file
        except Exception as e:
            if not self.quiet:
                logger.error(f"Failed to create .env file for {example_name}: {e}")
            return None
