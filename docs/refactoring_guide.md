# UnitMCP Refactoring Guide

This document outlines the refactoring work being done on the UnitMCP project, including the standardized utilities that have been implemented and how to use them in your code.

## Implemented Utilities

### 1. Exception Handling

A standardized exception hierarchy has been implemented in `src/unitmcp/utils/exceptions.py`. This provides a consistent way to handle errors across the codebase.

Key exceptions:
- `UnitMCPError`: Base exception for all errors
- `ConfigurationError`: Configuration-related errors
- `NetworkError`: Network-related errors
- `ResourceError`: Resource management errors
- `ExampleError`: Example-related errors
- `HardwareError`: Hardware-related errors
- `SecurityError`: Security-related errors
- `OrchestratorError`: Orchestrator-related errors
- `RemoteError`: Remote operation errors

Example usage:
```python
from unitmcp.utils import NetworkError

def connect_to_device(host, port):
    try:
        # Connection code here
        socket.connect((host, port))
    except socket.error as e:
        raise NetworkError(f"Failed to connect to {host}:{port}: {e}")
```

### 2. Resource Management

A resource management utility has been implemented in `src/unitmcp/utils/resource_manager.py`. This provides a context manager for tracking and cleaning up resources.

Key components:
- `ResourceManager`: Context manager for tracking and cleaning up resources
- `ManagedResource`: Protocol for resources that can be managed
- `safe_close`: Utility function for safely closing resources

Example usage:
```python
from unitmcp.utils import ResourceManager

def process_data():
    with ResourceManager() as rm:
        # Register resources with the manager
        file = rm.register(open("data.txt", "r"))
        connection = rm.register(connect_to_server())
        
        # Use resources
        data = file.read()
        connection.send(data)
        
        # Resources will be automatically cleaned up when the context manager exits
```

### 3. Logging Utilities

Standardized logging utilities have been implemented in `src/unitmcp/utils/logging_utils.py`. These provide a consistent way to configure logging and obtain loggers.

Key functions:
- `configure_logging`: Configure logging for the application
- `get_logger`: Get a logger with standardized settings
- `log_exception`: Log an exception with appropriate level
- `create_timed_rotating_logger`: Create a logger with timed rotation
- `log_method_call`: Decorator to log method calls

Example usage:
```python
from unitmcp.utils import configure_logging, get_standardized_logger, log_exception

# Configure logging at application startup
configure_logging(level="INFO", log_file="app.log", console=True)

# Get a logger for a module
logger = get_standardized_logger(__name__)

# Log messages
logger.info("Application started")
logger.debug("Processing data")

# Log exceptions
try:
    # Code that might raise an exception
    process_data()
except Exception as e:
    log_exception(logger, e, "Failed to process data")
```

### 4. Configuration Management

A configuration management utility has been implemented in `src/unitmcp/utils/config_manager.py`. This provides a unified interface for loading, validating, and saving configuration.

Key components:
- `ConfigManager`: Manager for loading and saving configuration
- `load_config`: Load configuration from a file
- `save_config`: Save configuration to a file
- `validate_config`: Validate configuration against a schema

Example usage:
```python
from unitmcp.utils import ConfigManager

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

## Refactored Examples

### Remote Shell

The `examples/shell_cli/refactored_remote_shell.py` file demonstrates how to use the standardized utilities in a real component. It includes:

- Proper exception handling with the standardized exception hierarchy
- Resource management with the `ResourceManager` class
- Standardized logging with the logging utilities
- Improved error handling and reporting
- Graceful degradation when utilities are not available

To run the refactored remote shell:
```bash
python examples/shell_cli/refactored_remote_shell.py --host <hostname> --port <port> [--ssh] [--simulation]
```

## Refactoring Guidelines

When refactoring existing code or writing new code, follow these guidelines:

1. **Use the standardized exception hierarchy**: Catch specific exceptions and raise appropriate exceptions from the hierarchy.

2. **Manage resources properly**: Use the `ResourceManager` to track and clean up resources, especially in complex code paths.

3. **Use standardized logging**: Configure logging using `configure_logging` and obtain loggers using `get_standardized_logger`.

4. **Document your code**: Follow the documentation standards in `docs/documentation_standards.md`.

5. **Handle errors gracefully**: Catch exceptions at appropriate levels and provide helpful error messages.

6. **Use configuration management**: Use the `ConfigManager` for loading and saving configuration.

7. **Write tests**: Ensure that your refactored code is well-tested, including error cases.

## Next Steps

The following components are planned for refactoring:

1. **Orchestrator**: Refactor the orchestrator to use the standardized utilities.

2. **Example Manager**: Refactor the example manager to use the standardized utilities.

3. **Hardware Interface**: Refactor the hardware interface to use the standardized utilities.

4. **Network Components**: Refactor network-related components to use the standardized utilities.

5. **Configuration Handling**: Refactor configuration handling to use the new `ConfigManager`.

## Contributing

When contributing to the refactoring effort, please follow these steps:

1. Identify a component to refactor.
2. Create a branch for your refactoring work.
3. Refactor the component to use the standardized utilities.
4. Write tests for the refactored component.
5. Update documentation to reflect the changes.
6. Submit a pull request for review.
