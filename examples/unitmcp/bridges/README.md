# UnitMCP Bridges Example

This directory contains a template for creating new examples in the UnitMCP project. It follows the standardized structure with client-server architecture and a runner to simplify startup.

## Structure

- `runner.py`: Manages the execution of the client and server components
- `client.py`: Implements the client-side functionality
- `server.py`: Implements the server-side functionality
- `config/`: Contains configuration files for the client and server
  - `client.yaml`: Client configuration
  - `server.yaml`: Server configuration
- `tests/`: Contains unit tests for the example

## How to Use This Template

1. Copy this entire directory to create a new example
2. Rename it to reflect your example's purpose
3. Modify the files to implement your specific functionality
4. Update this README.md with details about your example

## Running the Example

To run this example, execute the runner script:

```bash
python runner.py
```

This will start both the client and server components according to the configuration files.

## Configuration

The example can be configured by modifying the YAML files in the `config/` directory:

- `client.yaml`: Configure client-specific settings
- `server.yaml`: Configure server-specific settings

## Customization

When creating your own example based on this template:

1. Implement the server functionality in `server.py`
2. Implement the client functionality in `client.py`
3. Adjust the configuration files as needed
4. Update the runner if necessary for your specific needs

## Testing

The example includes unit tests in the `tests/` directory. Run them with:

```bash
python -m unittest discover tests
```
