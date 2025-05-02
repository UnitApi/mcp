#!/usr/bin/env python3
"""
Enhanced Configuration Loader with Environment Variable Support

This module provides a ConfigLoader class that can load YAML configuration files
and resolve environment variables within the configuration.
"""

import os
import re
import logging
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("UnitMCP-Config")

class ConfigLoader:
    """Loads and processes automation configuration with environment variable support."""
    
    def __init__(self, config_file: str, env_file: str = None):
        """Initialize the configuration loader.
        
        Args:
            config_file: Path to the YAML configuration file
            env_file: Path to the .env file (optional)
        """
        self.config_file = config_file
        self.env_file = env_file or os.path.join(os.path.dirname(os.path.abspath(config_file)), '.env')
        self.config = None
        
        # Load environment variables
        self._load_environment_variables()
        
    def _load_environment_variables(self):
        """Load environment variables from .env file if it exists."""
        if os.path.exists(self.env_file):
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
