"""Example manager module for UnitMCP Orchestrator."""

import os
import logging
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class ExampleManager:
    """
    Manager for UnitMCP examples.
    
    This class provides functionality to:
    - Discover available examples
    - Get example details
    - Create and manage example configurations
    - Copy examples to create new ones
    """
    
    def __init__(self, examples_dir: Optional[str] = None):
        """
        Initialize the ExampleManager.
        
        Args:
            examples_dir: Path to the examples directory. If None, uses default.
        """
        self.examples_dir = examples_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "examples")
        
        # Initialize example registry
        self.examples = {}
        
        # Discover available examples
        self.discover_examples()
        
        logger.info(f"ExampleManager initialized with {len(self.examples)} examples")
    
    def discover_examples(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available examples in the examples directory.
        
        Returns:
            Dictionary of examples with their details
        """
        self.examples = {}
        
        if not os.path.exists(self.examples_dir):
            logger.warning(f"Examples directory not found: {self.examples_dir}")
            return self.examples
        
        # Get all directories in examples directory
        for item in os.listdir(self.examples_dir):
            item_path = os.path.join(self.examples_dir, item)
            
            # Skip non-directories and special directories
            if not os.path.isdir(item_path) or item.startswith('.') or item.startswith('__'):
                continue
                
            # Check if directory contains a runner.py file or server.py file or start_server.py
            runner_path = os.path.join(item_path, "runner.py")
            server_path = os.path.join(item_path, "server.py")
            start_server_path = os.path.join(item_path, "start_server.py")
            
            if any(os.path.exists(p) for p in [runner_path, server_path, start_server_path]):
                # Read README.md for description if available
                readme_path = os.path.join(item_path, "README.md")
                description = ""
                
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, 'r') as f:
                            # Extract first paragraph from README
                            lines = []
                            for line in f:
                                if line.strip():
                                    lines.append(line.strip())
                                elif lines:  # Empty line after content
                                    break
                            
                            description = " ".join(lines)
                    except Exception as e:
                        logger.warning(f"Failed to read README for {item}: {e}")
                
                # Add example to registry
                self.examples[item] = {
                    "name": item,
                    "path": item_path,
                    "description": description,
                    "has_runner": os.path.exists(runner_path),
                    "has_server": os.path.exists(server_path),
                    "has_start_server": os.path.exists(start_server_path),
                    "env_file": os.path.join(item_path, ".env") if os.path.exists(os.path.join(item_path, ".env")) else None,
                    "env_example": os.path.join(item_path, ".env.example") if os.path.exists(os.path.join(item_path, ".env.example")) else None
                }
        
        return self.examples
    
    def get_examples(self) -> Dict[str, Dict[str, Any]]:
        """Get all available examples."""
        return self.examples
    
    def get_example(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific example by name."""
        return self.examples.get(name)
    
    def create_env_file(self, example_name: str, config: Dict[str, Any]) -> Optional[str]:
        """
        Create or update .env file for an example.
        
        Args:
            example_name: Name of the example
            config: Configuration dictionary with environment variables
            
        Returns:
            Path to the created .env file or None if failed
        """
        example = self.get_example(example_name)
        if not example:
            raise ValueError(f"Example '{example_name}' not found")
        
        # Start with example's .env.example if available
        env_content = {}
        if example["env_example"]:
            try:
                with open(example["env_example"], 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_content[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Failed to read .env.example for {example_name}: {e}")
        
        # Update with provided configuration
        env_content.update(config)
        
        # Write to .env file
        env_file = os.path.join(example["path"], ".env")
        try:
            with open(env_file, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            return env_file
        except Exception as e:
            logger.error(f"Failed to create .env file for {example_name}: {e}")
            return None
    
    def copy_example(self, source_name: str, target_name: str) -> Optional[Dict[str, Any]]:
        """
        Copy an example to create a new one.
        
        Args:
            source_name: Name of the source example
            target_name: Name of the target example
            
        Returns:
            Details of the new example or None if failed
        """
        source = self.get_example(source_name)
        if not source:
            raise ValueError(f"Source example '{source_name}' not found")
        
        # Check if target already exists
        target_path = os.path.join(self.examples_dir, target_name)
        if os.path.exists(target_path):
            raise ValueError(f"Target example '{target_name}' already exists")
        
        # Copy example directory
        try:
            shutil.copytree(source["path"], target_path)
            
            # Remove .env file if exists
            env_file = os.path.join(target_path, ".env")
            if os.path.exists(env_file):
                os.remove(env_file)
            
            # Update README if exists
            readme_path = os.path.join(target_path, "README.md")
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r') as f:
                        content = f.read()
                    
                    # Update title
                    content = content.replace(source_name, target_name)
                    
                    with open(readme_path, 'w') as f:
                        f.write(content)
                except Exception as e:
                    logger.warning(f"Failed to update README for {target_name}: {e}")
            
            # Rediscover examples to include the new one
            self.discover_examples()
            
            return self.get_example(target_name)
        except Exception as e:
            logger.error(f"Failed to copy example '{source_name}' to '{target_name}': {e}")
            return None
    
    def delete_example(self, name: str) -> bool:
        """
        Delete an example.
        
        Args:
            name: Name of the example to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        example = self.get_example(name)
        if not example:
            raise ValueError(f"Example '{name}' not found")
        
        try:
            shutil.rmtree(example["path"])
            
            # Rediscover examples to update registry
            self.discover_examples()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete example '{name}': {e}")
            return False
    
    def get_example_files(self, name: str) -> List[str]:
        """
        Get list of files in an example.
        
        Args:
            name: Name of the example
            
        Returns:
            List of file paths relative to the example directory
        """
        example = self.get_example(name)
        if not example:
            raise ValueError(f"Example '{name}' not found")
        
        files = []
        
        for root, _, filenames in os.walk(example["path"]):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, example["path"])
                files.append(rel_path)
        
        return files
    
    def get_example_file_content(self, name: str, file_path: str) -> Optional[str]:
        """
        Get content of a file in an example.
        
        Args:
            name: Name of the example
            file_path: Path to the file relative to the example directory
            
        Returns:
            File content or None if failed
        """
        example = self.get_example(name)
        if not example:
            raise ValueError(f"Example '{name}' not found")
        
        full_path = os.path.join(example["path"], file_path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise ValueError(f"File '{file_path}' not found in example '{name}'")
        
        try:
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file '{file_path}' in example '{name}': {e}")
            return None
    
    def update_example_file(self, name: str, file_path: str, content: str) -> bool:
        """
        Update content of a file in an example.
        
        Args:
            name: Name of the example
            file_path: Path to the file relative to the example directory
            content: New file content
            
        Returns:
            True if updated successfully, False otherwise
        """
        example = self.get_example(name)
        if not example:
            raise ValueError(f"Example '{name}' not found")
        
        full_path = os.path.join(example["path"], file_path)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            with open(full_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to update file '{file_path}' in example '{name}': {e}")
            return False
    
    def get_example_categories(self) -> Dict[str, List[str]]:
        """
        Group examples by categories.
        
        Returns:
            Dictionary with categories as keys and lists of example names as values
        """
        categories = {}
        
        for name, info in self.examples.items():
            # Try to determine category from directory structure or name
            category = "Other"
            
            # Check if example is in a subdirectory
            path_parts = os.path.relpath(info["path"], self.examples_dir).split(os.path.sep)
            if len(path_parts) > 1:
                category = path_parts[0]
            else:
                # Try to infer category from name
                if "rpi" in name.lower() or "raspberry" in name.lower():
                    category = "Raspberry Pi"
                elif "server" in name.lower():
                    category = "Server"
                elif "client" in name.lower():
                    category = "Client"
                elif "hardware" in name.lower():
                    category = "Hardware"
                elif "security" in name.lower():
                    category = "Security"
                elif "basic" in name.lower():
                    category = "Basic"
                elif "advanced" in name.lower():
                    category = "Advanced"
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(name)
        
        return categories
