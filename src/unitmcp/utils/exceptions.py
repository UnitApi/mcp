"""
Exception hierarchy for UnitMCP.

This module defines a standardized exception hierarchy for the UnitMCP project.
All custom exceptions should inherit from the base UnitMCPError class.

Classes:
    UnitMCPError: Base exception for all UnitMCP errors
    ConfigurationError: Error in configuration
    NetworkError: Network-related error
    ResourceError: Error related to resource management
    ExampleError: Error related to examples
    HardwareError: Error related to hardware interaction
    SecurityError: Error related to security operations
    
Example:
    ```python
    from unitmcp.utils.exceptions import ConfigurationError
    
    try:
        # Some operation that might fail
        load_config(config_file)
    except FileNotFoundError as e:
        # Wrap the original exception
        raise ConfigurationError(f"Configuration file not found: {config_file}") from e
    ```
"""

class UnitMCPError(Exception):
    """Base exception for all UnitMCP errors."""
    pass


class ConfigurationError(UnitMCPError):
    """
    Error in configuration.
    
    This exception is raised when there is an issue with configuration,
    such as missing or invalid configuration files or parameters.
    """
    pass


class NetworkError(UnitMCPError):
    """
    Network-related error.
    
    This exception is raised when there is an issue with network operations,
    such as connection failures, timeouts, or protocol errors.
    """
    pass


class ResourceError(UnitMCPError):
    """
    Error related to resource management.
    
    This exception is raised when there is an issue with resource management,
    such as failure to acquire or release resources, resource contention,
    or resource exhaustion.
    """
    pass


class ExampleError(UnitMCPError):
    """
    Error related to examples.
    
    This exception is raised when there is an issue with examples,
    such as missing example files, invalid example configuration,
    or failure to run an example.
    """
    pass


class HardwareError(UnitMCPError):
    """
    Error related to hardware interaction.
    
    This exception is raised when there is an issue with hardware interaction,
    such as device not found, communication failure, or hardware malfunction.
    """
    pass


class SecurityError(UnitMCPError):
    """
    Error related to security operations.
    
    This exception is raised when there is an issue with security operations,
    such as authentication failure, authorization error, or encryption failure.
    """
    pass


class OrchestratorError(UnitMCPError):
    """
    Error related to the orchestrator.
    
    This exception is raised when there is an issue with the orchestrator,
    such as failure to start or stop runners, or issues with example management.
    """
    pass


class RemoteError(UnitMCPError):
    """
    Error related to remote operations.
    
    This exception is raised when there is an issue with remote operations,
    such as SSH connection failures or remote command execution errors.
    """
    pass
