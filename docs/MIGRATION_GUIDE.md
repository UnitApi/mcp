# UnitMCP Migration Guide

This guide helps you migrate your existing UnitMCP projects to the new project structure.

## Overview of Changes

The UnitMCP project has undergone a significant reorganization to improve code organization, eliminate duplication, and enhance overall project clarity and usability. The main changes include:

1. **Unified Documentation Structure**: All documentation is now organized in the `docs/` directory with clear sections.
2. **Consolidated Configuration Files**: Configuration files are now organized in the `configs/` directory.
3. **Reorganized Examples**: Examples are now categorized by functionality.
4. **Standardized Source Code Structure**: Source code is now organized into logical categories.

## Migration Steps

### Step 1: Documentation Migration

If you have created custom documentation, move it to the appropriate location in the new structure:

```
docs/
├── api/                 # API documentation
├── architecture/        # Architecture documentation
│   ├── diagrams/        # Architecture diagrams
│   └── descriptions/    # Component descriptions
├── guides/              # User guides
│   ├── installation/    # Installation guides
│   ├── hardware/        # Hardware guides
│   └── llm/             # LLM integration guides
├── examples/            # Example documentation
└── development/         # Development documentation
```

### Step 2: Configuration Migration

Update your configuration file paths to match the new structure:

#### Old Structure:
```
.env
.env.development
.env.example
examples/dsl/device_config.yaml
examples/rpi_control/automation_config.yaml
```

#### New Structure:
```
configs/
├── env/                 # Environment variables
│   ├── default.env      # Default environment variables
│   ├── development.env  # Development environment variables
│   └── example.env      # Example environment variables
└── yaml/                # YAML configuration files
    ├── devices/         # Device configurations
    │   └── default.yaml # Default device configuration
    ├── automation/      # Automation configurations
    │   └── default.yaml # Default automation configuration
    └── security/        # Security configurations
```

Update your code to load configuration files from the new locations:

```python
# Old way
config_path = ".env"
yaml_path = "examples/dsl/device_config.yaml"

# New way
config_path = "configs/env/default.env"
yaml_path = "configs/yaml/devices/default.yaml"
```

### Step 3: Update Import Paths

If you have custom code that imports UnitMCP modules, you may need to update the import paths:

```python
# Old imports
from unitmcp.dsl import DslHardwareIntegration
from unitmcp.hardware import MCPHardwareClient

# New imports (if changed)
from unitmcp.core.dsl import DslHardwareIntegration
from unitmcp.hardware.client import MCPHardwareClient
```

### Step 4: Update Docker Configurations

If you're using Docker, update your Docker Compose files and Dockerfiles to use the new configuration paths:

```yaml
# Old
volumes:
  - ./.env:/app/.env

# New
volumes:
  - ./configs/env/default.env:/app/configs/env/default.env
```

### Step 5: Update CI/CD Configurations

If you have CI/CD pipelines, update the paths in your configuration files:

```yaml
# Old
- name: Load configuration
  run: cp .env.example .env

# New
- name: Load configuration
  run: cp configs/env/example.env configs/env/default.env
```

## Compatibility Layer

To ease migration, UnitMCP temporarily includes a compatibility layer that allows old paths to work with the new structure. However, this compatibility layer will be removed in a future release, so it's recommended to update your code as soon as possible.

The compatibility layer includes:

- Symlinks from old paths to new paths
- Automatic path resolution for common configuration files
- Deprecation warnings when using old paths

## Frequently Asked Questions

### Q: Will my existing code still work?

A: Yes, the compatibility layer ensures that existing code will continue to work, but you will see deprecation warnings. It's recommended to update your code to use the new paths.

### Q: How do I verify that my migration was successful?

A: Run the verification script to check if your migration was successful:

```bash
python scripts/verify_migration.py
```

### Q: What if I encounter issues during migration?

A: If you encounter issues during migration, check the troubleshooting section in the documentation or open an issue on GitHub.

## Timeline

- **Phase 1 (Current)**: Documentation and configuration migration
- **Phase 2 (Coming Soon)**: Source code reorganization
- **Phase 3 (Future)**: Removal of compatibility layer

## Need Help?

If you need help with migration, please:

1. Check the documentation
2. Join our community Discord server
3. Open an issue on GitHub
4. Contact the maintainers
