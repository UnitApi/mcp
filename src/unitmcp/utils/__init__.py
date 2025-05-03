"""Utility functions for UnitMCP."""

from .logger import get_logger, setup_logging
from .env_loader import EnvLoader, ConfigLoader, env, get_rpi_host, get_rpi_port, get_log_level, get_log_file, get_default_led_pin, get_default_button_pin, get_simulation_mode, get_automation_duration, get_audio_dir, get_default_volume
from .exceptions import (
    UnitMCPError, ConfigurationError, NetworkError, ResourceError, 
    ExampleError, HardwareError, SecurityError, OrchestratorError, RemoteError
)
from .resource_manager import ResourceManager, ManagedResource, safe_close
from .logging_utils import (
    configure_logging, get_logger as get_standardized_logger, 
    log_exception, create_timed_rotating_logger, log_method_call
)
from .config_manager import ConfigManager, load_config, save_config, validate_config

__all__ = [
    # Logger utilities
    "get_logger",
    "setup_logging",
    "configure_logging",
    "get_standardized_logger",
    "log_exception",
    "create_timed_rotating_logger",
    "log_method_call",
    
    # Environment and configuration
    "EnvLoader",
    "ConfigLoader",
    "env",
    "get_rpi_host",
    "get_rpi_port",
    "get_log_level",
    "get_log_file",
    "get_default_led_pin",
    "get_default_button_pin",
    "get_simulation_mode",
    "get_automation_duration",
    "get_audio_dir",
    "get_default_volume",
    
    # Configuration management
    "ConfigManager",
    "load_config",
    "save_config",
    "validate_config",
    
    # Resource management
    "ResourceManager",
    "ManagedResource",
    "safe_close",
    
    # Exceptions
    "UnitMCPError",
    "ConfigurationError",
    "NetworkError",
    "ResourceError",
    "ExampleError",
    "HardwareError",
    "SecurityError",
    "OrchestratorError",
    "RemoteError",
]
