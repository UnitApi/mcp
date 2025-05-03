# UnitMCP Installation Guide

This guide provides instructions for installing UnitMCP on various platforms.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Installation Methods

### Method 1: Install from PyPI

The simplest way to install UnitMCP is from PyPI:

```bash
pip install unitmcp
```

### Method 2: Install from Source

For the latest development version, you can install from source:

```bash
git clone https://github.com/yourusername/UnitApi.git
cd UnitApi/mcp
pip install -e .
```

## Platform-Specific Instructions

### Raspberry Pi

For Raspberry Pi installations, additional dependencies may be required:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip libopenjp2-7 libtiff5

# Install UnitMCP
pip3 install unitmcp
```

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip

# Install UnitMCP
pip3 install unitmcp
```

### macOS

```bash
# Install using pip
pip3 install unitmcp
```

### Windows

```bash
# Install using pip
pip install unitmcp
```

## Configuration

After installation, you'll need to configure UnitMCP. See the [Configuration Guide](../configuration/README.md) for details.

## Troubleshooting

If you encounter issues during installation, check the following:

1. Ensure you have the correct Python version: `python --version`
2. Check for dependency conflicts: `pip check`
3. Try installing with verbose output: `pip install -v unitmcp`

For more help, see the [Troubleshooting Guide](../troubleshooting/README.md).
