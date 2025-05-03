# UnitMCP API Documentation

This directory contains API documentation for the UnitMCP project.

## Overview

The UnitMCP API provides a comprehensive interface for hardware control through the Model Context Protocol (MCP). This documentation covers all public APIs, their usage, and examples.

## API Modules

- **Hardware Client API**: Interface for controlling hardware devices
- **Server API**: Interface for the UnitMCP server
- **DSL API**: Interface for the Domain-Specific Language
- **Plugin API**: Interface for the plugin system, including the Claude UnitMCP Plugin

## Getting Started

To use the UnitMCP API, first import the appropriate modules:

```python
from unitmcp.hardware.client import MCPHardwareClient
from unitmcp.dsl.integration import DslHardwareIntegration
from unitmcp.plugin.main import ClaudeUnitMCPPlugin
```

Then create an instance of the client and connect to the hardware:

```python
client = MCPHardwareClient()
await client.connect()
```

See the individual module documentation for more details on specific APIs.
