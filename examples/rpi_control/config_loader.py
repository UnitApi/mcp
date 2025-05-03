#!/usr/bin/env python3
"""
Enhanced Configuration Loader with Environment Variable Support

This module provides a ConfigLoader class that can load YAML configuration files
and resolve environment variables within the configuration.

NOTE: This is a simplified version for examples. For production use,
import the ConfigLoader from unitmcp.utils.env_loader instead.
"""

import os
import re
import logging
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("UnitMCP-Config")

class ConfigLoader:
    """Loads and processes automation configuration with environment variable support."""
    
    def __init__(self, config_file: str = None, env_file: str = None, config_type: str = None):
        """Initialize the configuration loader.
        
        Args:
            config_file: Path to the YAML configuration file (optional)
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
        
        # Set default env file if not provided
        if not env_file and self.project_root:
            self.env_file = os.path.join(self.project_root, "configs", "env", "default.env")
        else:
            self.env_file = env_file
        
        self.config = None
        
        # Load environment variables
        self._load_environment_variables()
        
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
        
    def _load_environment_variables(self):
        """Load environment variables from .env file if it exists."""
        if self.env_file and os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment variables from {self.env_file}")
        else:
            logger.debug(f"No .env file found at {self.env_file}")
        
    def _resolve_env_vars(self, value):
        """Recursively resolve environment variables in configuration values.
        
        Supports both ${VAR} and $VAR formats.
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
            return {k: self._resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_env_vars(item) for item in value]
        else:
            return value
        
    def load_config(self) -> Dict[str, Any]:
        """Load the configuration from the YAML file and resolve environment variables.
        
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
            self.config = self._resolve_env_vars(self.config)
            
            logger.info(f"Loaded configuration from {self.config_file}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
