#!/usr/bin/env python3
"""
Environment Variable Loader for UnitMCP

This module provides utilities for loading and accessing environment variables
from .env files and the system environment. It provides a consistent way to
handle environment variables across all UnitMCP examples and applications.
"""

import os
import re
import logging
import yaml
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("UnitMCP-Env")

class EnvLoader:
    """Handles loading and accessing environment variables for UnitMCP applications."""
    
    def __init__(self, env_file: Optional[str] = None, search_paths: Optional[List[str]] = None):
        """Initialize the environment variable loader.
        
        Args:
            env_file: Path to the .env file (optional)
            search_paths: List of paths to search for .env files (optional)
        """
        self.env_file = env_file
        self.search_paths = search_paths or []
        self.loaded = False
        
        # Default configs directory
        self.configs_dir = os.path.join(self._find_project_root() or "", "configs", "env")
        
        # Load environment variables
        self.load_env()
        
    def load_env(self) -> bool:
        """Load environment variables from .env files.
        
        Returns:
            True if environment variables were loaded, False otherwise
        """
        # If a specific env_file was provided, try to load it
        if self.env_file and os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment variables from {self.env_file}")
            self.loaded = True
            return True
            
        # Otherwise, search for .env files in the search paths
        for path in self.search_paths:
            env_path = os.path.join(path, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                self.loaded = True
                return True
        
        # Try to load from the new configs/env directory
        if os.path.exists(self.configs_dir):
            # Try default.env first
            default_env_path = os.path.join(self.configs_dir, 'default.env')
            if os.path.exists(default_env_path):
                load_dotenv(default_env_path)
                logger.info(f"Loaded environment variables from {default_env_path}")
                self.loaded = True
                return True
                
            # Try development.env if default.env doesn't exist
            dev_env_path = os.path.join(self.configs_dir, 'development.env')
            if os.path.exists(dev_env_path):
                load_dotenv(dev_env_path)
                logger.info(f"Loaded environment variables from {dev_env_path}")
                self.loaded = True
                return True
                
        # If no .env file was found, try to load from the current directory (legacy support)
        if os.path.exists('.env'):
            load_dotenv('.env')
            logger.info("Loaded environment variables from ./.env")
            self.loaded = True
            return True
            
        # If no .env file was found, try to load from the project root (legacy support)
        project_root = self._find_project_root()
        if project_root:
            env_path = os.path.join(project_root, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                self.loaded = True
                return True
                
        logger.debug("No .env file found")
        return False
        
    def _find_project_root(self) -> Optional[str]:
        """Find the project root directory by looking for setup.py or pyproject.toml.
        
        Returns:
            Path to the project root directory, or None if not found
        """
        current_dir = os.path.abspath(os.path.curdir)
        
        # Walk up the directory tree looking for setup.py or pyproject.toml
        while current_dir != os.path.dirname(current_dir):  # Stop at the root directory
            if os.path.exists(os.path.join(current_dir, 'setup.py')) or \
               os.path.exists(os.path.join(current_dir, 'pyproject.toml')):
                return current_dir
            current_dir = os.path.dirname(current_dir)
            
        return None
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get an environment variable.
        
        Args:
            key: Name of the environment variable
            default: Default value to return if the environment variable is not set
            
        Returns:
            Value of the environment variable, or the default value if not set
        """
        return os.environ.get(key, default)
        
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an environment variable as an integer.
        
        Args:
            key: Name of the environment variable
            default: Default value to return if the environment variable is not set
            
        Returns:
            Value of the environment variable as an integer, or the default value if not set
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Environment variable {key} is not a valid integer: {value}")
            return default
            
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get an environment variable as a float.
        
        Args:
            key: Name of the environment variable
            default: Default value to return if the environment variable is not set
            
        Returns:
            Value of the environment variable as a float, or the default value if not set
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Environment variable {key} is not a valid float: {value}")
            return default
            
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get an environment variable as a boolean.
        
        Args:
            key: Name of the environment variable
            default: Default value to return if the environment variable is not set
            
        Returns:
            Value of the environment variable as a boolean, or the default value if not set
        """
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ['true', '1', 'yes', 'y', 'on']
        
    def get_list(self, key: str, default: List[str] = None, separator: str = ',') -> List[str]:
        """Get an environment variable as a list.
        
        Args:
            key: Name of the environment variable
            default: Default value to return if the environment variable is not set
            separator: Separator to split the environment variable value
            
        Returns:
            Value of the environment variable as a list, or the default value if not set
        """
        default = default or []
        value = os.environ.get(key)
        if value is None:
            return default
        return [item.strip() for item in value.split(separator)]
        
    def resolve_env_vars(self, value: Any) -> Any:
        """Recursively resolve environment variables in values.
        
        Supports both ${VAR} and $VAR formats.
        
        Args:
            value: Value to resolve environment variables in
            
        Returns:
            Value with environment variables resolved
        """
        if isinstance(value, str):
            # Match ${VAR} format
            pattern1 = r'\${([A-Za-z0-9_]+)}'
            matches1 = re.findall(pattern1, value)
            result = value
            
            for match in matches1:
                env_value = os.environ.get(match, f"${{{match}}}")
                result = result.replace(f"${{{match}}}", env_value)
            
            # Match $VAR format
            pattern2 = r'(?<!\$)\$([A-Za-z0-9_]+)'
            matches2 = re.findall(pattern2, result)
            
            for match in matches2:
                env_value = os.environ.get(match, f"${match}")
                result = result.replace(f"${match}", env_value)
                
            return result
        elif isinstance(value, dict):
            return {k: self.resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_env_vars(item) for item in value]
        elif isinstance(value, set):
            return {self.resolve_env_vars(item) for item in value}
        elif isinstance(value, tuple):
            return tuple(self.resolve_env_vars(item) for item in value)
        else:
            return value


class ConfigLoader:
    """Loads and processes configuration files with environment variable support."""
    
    def __init__(self, config_file: str = None, env_file: str = None, config_type: str = None):
        """Initialize the configuration loader.
        
        Args:
            config_file: Path to the configuration file (optional)
            env_file: Path to the .env file (optional)
            config_type: Type of configuration (devices, automation, security) (optional)
        """
        self.config_file = config_file
        self.config_type = config_type
        
        # Find project root
        self.project_root = self._find_project_root()
        
        # Set up configs directory paths
        if self.project_root:
            self.configs_yaml_dir = os.path.join(self.project_root, "configs", "yaml")
            
            # If config_file is not provided but config_type is, use the default config file for that type
            if not config_file and config_type:
                if config_type in ["devices", "automation", "security"]:
                    self.config_file = os.path.join(self.configs_yaml_dir, config_type, "default.yaml")
        
        # Set up environment loader
        search_paths = []
        if self.config_file:
            search_paths.append(os.path.dirname(os.path.abspath(self.config_file)))
        
        self.env_loader = EnvLoader(env_file, search_paths)
        self.config = None
        
    def _find_project_root(self) -> Optional[str]:
        """Find the project root directory by looking for setup.py or pyproject.toml.
        
        Returns:
            Path to the project root directory, or None if not found
        """
        current_dir = os.path.abspath(os.path.dirname(__file__))
        
        # Go up the directory tree until we find setup.py or pyproject.toml
        while current_dir != os.path.dirname(current_dir):  # Stop at the root directory
            if os.path.exists(os.path.join(current_dir, 'setup.py')) or \
               os.path.exists(os.path.join(current_dir, 'pyproject.toml')):
                return current_dir
            current_dir = os.path.dirname(current_dir)
            
        return None
        
    def load_yaml_config(self) -> Dict[str, Any]:
        """Load a YAML configuration file and resolve environment variables.
        
        Returns:
            Dictionary containing the processed configuration
        """
        # If config_file is not set, try to find a default config file
        if not self.config_file and self.project_root and self.config_type:
            default_config = os.path.join(self.configs_yaml_dir, self.config_type, "default.yaml")
            if os.path.exists(default_config):
                self.config_file = default_config
                logger.info(f"Using default configuration file: {default_config}")
        
        if not self.config_file or not os.path.exists(self.config_file):
            logger.error("Configuration file not found")
            return {}
            
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
                
            # Process environment variables in the configuration
            self.config = self.env_loader.resolve_env_vars(self.config)
            
            logger.info(f"Loaded configuration from {self.config_file}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
            
    def load_config(self) -> Dict[str, Any]:
        """Load the configuration file and resolve environment variables.
        
        This method detects the file type based on the extension and calls the
        appropriate loader method.
        
        Returns:
            Dictionary containing the processed configuration
        """
        if not self.config_file:
            logger.error("No configuration file specified")
            return {}
            
        # Detect file type based on extension
        if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
            return self.load_yaml_config()
        else:
            logger.error(f"Unsupported configuration file format: {self.config_file}")
            return {}


# Create a singleton instance for easy access
env = EnvLoader()

# Helper functions for common environment variables
def get_rpi_host() -> str:
    """Get the Raspberry Pi hostname or IP address."""
    return env.get("RPI_HOST", "127.0.0.1")
    
def get_rpi_port() -> int:
    """Get the Raspberry Pi port."""
    return env.get_int("RPI_PORT", 8888)
    
def get_log_level() -> str:
    """Get the log level."""
    return env.get("LOG_LEVEL", "INFO")
    
def get_log_file() -> str:
    """Get the log file path."""
    return env.get("LOG_FILE", "unitmcp.log")
    
def get_default_led_pin() -> int:
    """Get the default LED pin."""
    return env.get_int("DEFAULT_LED_PIN", 17)
    
def get_default_button_pin() -> int:
    """Get the default button pin."""
    return env.get_int("DEFAULT_BUTTON_PIN", 23)
    
def get_simulation_mode() -> bool:
    """Get whether simulation mode is enabled."""
    return env.get_bool("SIMULATION_MODE", False)
    
def get_automation_duration() -> float:
    """Get the automation duration in seconds."""
    return env.get_float("AUTOMATION_DURATION", 30.0)
    
def get_audio_dir() -> str:
    """Get the audio directory."""
    return env.get("DEFAULT_AUDIO_DIR", "/tmp/sounds")
    
def get_default_volume() -> int:
    """Get the default volume."""
    return env.get_int("DEFAULT_VOLUME", 80)
