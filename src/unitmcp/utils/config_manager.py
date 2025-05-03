"""
Configuration management utilities for UnitMCP.

This module provides standardized configuration management for the UnitMCP project,
including loading, validating, and saving configuration from various sources.

Classes:
    ConfigManager: Manager for loading and saving configuration

Functions:
    load_config: Load configuration from a file
    save_config: Save configuration to a file
    validate_config: Validate configuration against a schema

Example:
    ```python
    from unitmcp.utils.config_manager import ConfigManager
    
    # Create a config manager with default values
    config_manager = ConfigManager(
        config_file="~/.unitmcp/config.json",
        defaults={"simulation": True, "log_level": "INFO"}
    )
    
    # Load configuration
    config = config_manager.load()
    
    # Use configuration
    simulation_mode = config.get("simulation", True)
    
    # Update and save configuration
    config["simulation"] = False
    config_manager.save(config)
    ```
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

from .exceptions import ConfigurationError
from .logging_utils import get_logger

logger = get_logger(__name__)


def load_config(
    config_file: str,
    default_config: Optional[Dict[str, Any]] = None,
    create_if_missing: bool = True,
    file_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        config_file: Path to the configuration file
        default_config: Default configuration to use if file doesn't exist
        create_if_missing: Whether to create the file with default config if missing
        file_format: Format of the file (json, yaml, or None to detect from extension)
        
    Returns:
        Loaded configuration
        
    Raises:
        ConfigurationError: If the configuration file cannot be loaded
    """
    # Expand user directory if needed
    config_file = os.path.expanduser(config_file)
    
    # Determine file format if not specified
    if file_format is None:
        _, ext = os.path.splitext(config_file)
        if ext.lower() in ['.yaml', '.yml']:
            file_format = 'yaml'
        else:
            file_format = 'json'
    
    # Check if file exists
    if not os.path.exists(config_file):
        if default_config is not None and create_if_missing:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # Save default configuration
            save_config(config_file, default_config, file_format=file_format)
            return default_config.copy()
        elif default_config is not None:
            return default_config.copy()
        else:
            raise ConfigurationError(f"Configuration file not found: {config_file}")
    
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            if file_format == 'yaml':
                return yaml.safe_load(f) or {}
            else:
                return json.load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration file: {e}") from e


def save_config(
    config_file: str,
    config: Dict[str, Any],
    file_format: Optional[str] = None,
    pretty: bool = True
) -> None:
    """
    Save configuration to a file.
    
    Args:
        config_file: Path to the configuration file
        config: Configuration to save
        file_format: Format of the file (json, yaml, or None to detect from extension)
        pretty: Whether to format the output for readability
        
    Raises:
        ConfigurationError: If the configuration file cannot be saved
    """
    # Expand user directory if needed
    config_file = os.path.expanduser(config_file)
    
    # Determine file format if not specified
    if file_format is None:
        _, ext = os.path.splitext(config_file)
        if ext.lower() in ['.yaml', '.yml']:
            file_format = 'yaml'
        else:
            file_format = 'json'
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            if file_format == 'yaml':
                yaml.dump(config, f, default_flow_style=False)
            else:
                if pretty:
                    json.dump(config, f, indent=2)
                else:
                    json.dump(config, f)
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration file: {e}") from e


def validate_config(
    config: Dict[str, Any],
    schema: Dict[str, Any],
    raise_on_error: bool = True
) -> List[str]:
    """
    Validate configuration against a schema.
    
    Args:
        config: Configuration to validate
        schema: Schema to validate against
        raise_on_error: Whether to raise an exception on validation error
        
    Returns:
        List of validation errors, empty if validation succeeds
        
    Raises:
        ConfigurationError: If validation fails and raise_on_error is True
    """
    errors = []
    
    # Check required fields
    for key, field_schema in schema.items():
        if field_schema.get('required', False) and key not in config:
            errors.append(f"Missing required field: {key}")
    
    # Validate fields
    for key, value in config.items():
        if key in schema:
            field_schema = schema[key]
            
            # Check type
            expected_type = field_schema.get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field {key} must be a string")
                elif expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Field {key} must be an integer")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field {key} must be a number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field {key} must be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field {key} must be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field {key} must be an object")
            
            # Check enum
            enum_values = field_schema.get('enum')
            if enum_values and value not in enum_values:
                errors.append(f"Field {key} must be one of: {', '.join(str(v) for v in enum_values)}")
            
            # Check minimum/maximum for numbers
            if isinstance(value, (int, float)):
                minimum = field_schema.get('minimum')
                if minimum is not None and value < minimum:
                    errors.append(f"Field {key} must be at least {minimum}")
                
                maximum = field_schema.get('maximum')
                if maximum is not None and value > maximum:
                    errors.append(f"Field {key} must be at most {maximum}")
            
            # Check minLength/maxLength for strings
            if isinstance(value, str):
                min_length = field_schema.get('minLength')
                if min_length is not None and len(value) < min_length:
                    errors.append(f"Field {key} must be at least {min_length} characters")
                
                max_length = field_schema.get('maxLength')
                if max_length is not None and len(value) > max_length:
                    errors.append(f"Field {key} must be at most {max_length} characters")
            
            # Check minItems/maxItems for arrays
            if isinstance(value, list):
                min_items = field_schema.get('minItems')
                if min_items is not None and len(value) < min_items:
                    errors.append(f"Field {key} must have at least {min_items} items")
                
                max_items = field_schema.get('maxItems')
                if max_items is not None and len(value) > max_items:
                    errors.append(f"Field {key} must have at most {max_items} items")
            
            # Check pattern for strings
            if isinstance(value, str) and 'pattern' in field_schema:
                import re
                pattern = field_schema['pattern']
                if not re.match(pattern, value):
                    errors.append(f"Field {key} must match pattern: {pattern}")
            
            # Validate nested objects
            if isinstance(value, dict) and 'properties' in field_schema:
                nested_errors = validate_config(
                    value,
                    field_schema['properties'],
                    raise_on_error=False
                )
                for error in nested_errors:
                    errors.append(f"{key}.{error}")
            
            # Validate array items
            if isinstance(value, list) and 'items' in field_schema:
                item_schema = field_schema['items']
                for i, item in enumerate(value):
                    if isinstance(item, dict) and isinstance(item_schema, dict):
                        nested_errors = validate_config(
                            item,
                            item_schema,
                            raise_on_error=False
                        )
                        for error in nested_errors:
                            errors.append(f"{key}[{i}].{error}")
    
    if errors and raise_on_error:
        raise ConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return errors


class ConfigManager:
    """
    Manager for loading and saving configuration.
    
    This class provides a unified interface for loading, validating,
    and saving configuration from various sources.
    """
    
    def __init__(
        self,
        config_file: str,
        defaults: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None,
        file_format: Optional[str] = None,
        auto_save: bool = True,
        validate_on_load: bool = True,
        environment_prefix: Optional[str] = None
    ):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
            defaults: Default configuration values
            schema: Schema for configuration validation
            file_format: Format of the configuration file (json, yaml, or None to detect from extension)
            auto_save: Whether to automatically save changes
            validate_on_load: Whether to validate configuration on load
            environment_prefix: Prefix for environment variables to override configuration
        """
        self.config_file = os.path.expanduser(config_file)
        self.defaults = defaults or {}
        self.schema = schema
        self.file_format = file_format
        self.auto_save = auto_save
        self.validate_on_load = validate_on_load
        self.environment_prefix = environment_prefix
        self.config = None
    
    def load(self, reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration.
        
        Args:
            reload: Whether to reload configuration even if already loaded
            
        Returns:
            Loaded configuration
        """
        if self.config is None or reload:
            # Load from file
            self.config = load_config(
                self.config_file,
                default_config=self.defaults,
                file_format=self.file_format
            )
            
            # Apply environment variables
            if self.environment_prefix:
                self._apply_environment_variables()
            
            # Validate configuration
            if self.validate_on_load and self.schema:
                validate_config(self.config, self.schema)
        
        return self.config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration.
        
        Args:
            config: Configuration to save, if None, uses the current configuration
        """
        if config is not None:
            self.config = config
        
        if self.config is not None:
            save_config(
                self.config_file,
                self.config,
                file_format=self.file_format
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        if self.config is None:
            self.load()
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        if self.config is None:
            self.load()
        
        self.config[key] = value
        
        if self.auto_save:
            self.save()
    
    def update(self, values: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            values: Dictionary of configuration values to update
        """
        if self.config is None:
            self.load()
        
        self.config.update(values)
        
        if self.auto_save:
            self.save()
    
    def _apply_environment_variables(self) -> None:
        """Apply environment variables to override configuration."""
        if not self.environment_prefix or not self.config:
            return
        
        prefix = self.environment_prefix.upper()
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Skip if empty
                if not config_key:
                    continue
                
                # Convert value to appropriate type
                if value.lower() in ['true', 'yes', '1']:
                    typed_value = True
                elif value.lower() in ['false', 'no', '0']:
                    typed_value = False
                elif value.isdigit():
                    typed_value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                    typed_value = float(value)
                else:
                    typed_value = value
                
                # Update configuration
                self.config[config_key] = typed_value
