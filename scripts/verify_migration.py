#!/usr/bin/env python3
"""
Verification script for UnitMCP project migration.
This script checks if the migration was successful by verifying that all required
files and directories exist in the new structure.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Define the expected structure after migration
EXPECTED_STRUCTURE = {
    "docs": {
        "api": ["README.md"],
        "architecture": {
            "diagrams": ["architecture.svg", "graph.svg", "project.svg"],
            "descriptions": ["DSL_INTEGRATION.md"]
        },
        "guides": {
            "installation": ["README.md"],
            "hardware": ["README.md"],
            "llm": ["claude_integration.md", "ollama_integration.md"]
        },
        "examples": [],
        "development": []
    },
    "configs": {
        "env": ["default.env", "development.env", "example.env"],
        "yaml": {
            "devices": ["default.yaml"],
            "automation": ["default.yaml", "env_automation.yaml"],
            "security": []
        }
    }
}

# Define the old paths that should have been migrated
OLD_PATHS = [
    "docs/DSL_INTEGRATION.md",
    "docs/architecture.svg",
    "docs/graph.svg",
    "docs/project.svg",
    ".env",
    ".env.development",
    ".env.example",
    "examples/dsl/device_config.yaml",
    "examples/rpi_control/automation_config.yaml",
    "examples/rpi_control/env_automation_config.yaml"
]

def check_directory_structure(base_path: Path, structure: Dict[str, Any]) -> List[str]:
    """
    Check if the directory structure matches the expected structure.
    
    Args:
        base_path: The base path to check
        structure: The expected structure
        
    Returns:
        A list of missing files or directories
    """
    missing = []
    
    for key, value in structure.items():
        path = base_path / key
        
        if not path.exists():
            missing.append(str(path))
            continue
            
        if isinstance(value, dict):
            # If the value is a dictionary, it represents a subdirectory
            missing.extend(check_directory_structure(path, value))
        elif isinstance(value, list):
            # If the value is a list, it represents files in the directory
            for file in value:
                file_path = path / file
                if not file_path.exists():
                    missing.append(str(file_path))
                    
    return missing

def check_old_paths(base_path: Path, old_paths: List[str]) -> List[str]:
    """
    Check if the old paths still exist.
    
    Args:
        base_path: The base path to check
        old_paths: The list of old paths to check
        
    Returns:
        A list of old paths that still exist
    """
    existing = []
    
    for path in old_paths:
        full_path = base_path / path
        if full_path.exists():
            existing.append(str(full_path))
            
    return existing

def main() -> int:
    """
    Main function to verify the migration.
    
    Returns:
        0 if successful, 1 otherwise
    """
    # Get the base path
    base_path = Path("/home/tom/github/UnitApi/mcp")
    
    # Check if the new structure exists
    print("Checking if the new structure exists...")
    missing = check_directory_structure(base_path, EXPECTED_STRUCTURE)
    
    if missing:
        print("The following files or directories are missing:")
        for path in missing:
            print(f"  - {path}")
        return 1
    
    print("All required files and directories exist in the new structure.")
    
    # Check if the old paths still exist (they should not if they were moved)
    print("\nChecking if the old paths still exist...")
    existing = check_old_paths(base_path, OLD_PATHS)
    
    if existing:
        print("The following old paths still exist:")
        for path in existing:
            print(f"  - {path}")
        print("\nWarning: The old paths still exist. This may cause confusion.")
        print("You may want to remove them after verifying that the migration was successful.")
    else:
        print("None of the old paths exist. This is good!")
    
    print("\nMigration verification completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
