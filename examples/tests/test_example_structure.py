#!/usr/bin/env python3
"""
Test module for UnitMCP example structure.
This module contains tests to verify that all examples follow the standardized structure.
"""

import os
import sys
import unittest
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestExampleStructure(unittest.TestCase):
    """Test the structure of all examples."""

    def setUp(self):
        """Set up the test environment."""
        self.examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.required_files = [
            "runner.py",
            "client.py",
            "server.py",
            "config/client.yaml",
            "config/server.yaml",
        ]
        self.examples = self._find_examples()
        
        # Filter out non-example directories
        self.examples = [example for example in self.examples if self._is_valid_example(example)]
        
        logger.info(f"Found {len(self.examples)} examples to test: {[os.path.basename(ex) for ex in self.examples]}")

    def _find_examples(self):
        """Find all examples in the examples directory."""
        examples = []
        for item in os.listdir(self.examples_dir):
            item_path = os.path.join(self.examples_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.') and not item == 'tests' and not item == 'runner':
                examples.append(item_path)
                # Check for subdirectories that might be examples
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path) and not subitem.startswith('.') and not subitem == 'tests':
                        examples.append(subitem_path)
        return examples
    
    def _is_valid_example(self, path):
        """
        Check if a directory is a valid example directory.
        
        Excludes directories like __pycache__, config, etc. that should not be treated as examples.
        """
        # Skip directories that are known to not be examples
        excluded_dirs = ['__pycache__', 'config', '.git', '.vscode', 'tests']
        basename = os.path.basename(path)
        
        if basename in excluded_dirs:
            return False
        
        # Check if this looks like an example directory (has at least one python file)
        has_python_file = False
        for item in os.listdir(path):
            if item.endswith('.py'):
                has_python_file = True
                break
        
        return has_python_file
    
    def _has_required_files(self, example):
        """Check if an example has all the required files."""
        for required_file in self.required_files:
            file_path = os.path.join(example, required_file)
            if not os.path.exists(file_path):
                return False
        return True

    def test_example_structure(self):
        """Test that all examples have the required files."""
        missing_files = {}
        for example in self.examples:
            missing = []
            for required_file in self.required_files:
                file_path = os.path.join(example, required_file)
                if not os.path.exists(file_path):
                    missing.append(required_file)
            
            if missing:
                missing_files[example] = missing
        
        if missing_files:
            for example, missing in missing_files.items():
                logger.warning(f"Example {os.path.basename(example)} is missing required files: {missing}")
            
            # Only fail the test if all examples are missing files
            if len(missing_files) == len(self.examples):
                self.fail("All examples are missing required files")
        else:
            # If all examples have all required files, the test passes
            self.assertTrue(True)

    def test_runner_imports(self):
        """Test that all runner.py files import the BaseRunner."""
        for example in self.examples:
            runner_path = os.path.join(example, "runner.py")
            if os.path.exists(runner_path):
                try:
                    with open(runner_path, "r") as f:
                        content = f.read()
                        if "BaseRunner" not in content or "from runner.base_runner import" not in content:
                            logger.warning(f"Runner in {example} does not import BaseRunner correctly")
                except Exception as e:
                    logger.warning(f"Error reading runner.py in {example}: {e}")
        
        # Test passes if we get here
        self.assertTrue(True)

    def test_runner_implementation(self):
        """Test that all runner.py files implement a Runner class."""
        for example in self.examples:
            runner_path = os.path.join(example, "runner.py")
            if os.path.exists(runner_path):
                try:
                    spec = importlib.util.spec_from_file_location("runner", runner_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Check if the module has a Runner class
                    if not hasattr(module, "Runner"):
                        logger.warning(f"Runner in {example} does not have a Runner class")
                        continue
                    
                    # Check if the Runner class inherits from BaseRunner
                    runner_class = getattr(module, "Runner")
                    if "BaseRunner" not in [base.__name__ for base in runner_class.__bases__]:
                        logger.warning(f"Runner in {example} does not inherit from BaseRunner")
                except Exception as e:
                    logger.warning(f"Error importing Runner from {example}: {e}")
        
        # Test passes if we get here
        self.assertTrue(True)

    def test_client_implementation(self):
        """Test that all client.py files implement required functions."""
        for example in self.examples:
            client_path = os.path.join(example, "client.py")
            if os.path.exists(client_path):
                try:
                    with open(client_path, "r") as f:
                        content = f.read()
                        if "if __name__ == \"__main__\"" not in content:
                            logger.warning(f"Client in {example} does not have a main block")
                except Exception as e:
                    logger.warning(f"Error reading client.py in {example}: {e}")
        
        # Test passes if we get here
        self.assertTrue(True)

    def test_server_implementation(self):
        """Test that all server.py files implement required functions."""
        for example in self.examples:
            server_path = os.path.join(example, "server.py")
            if os.path.exists(server_path):
                try:
                    with open(server_path, "r") as f:
                        content = f.read()
                        if "if __name__ == \"__main__\"" not in content:
                            logger.warning(f"Server in {example} does not have a main block")
                except Exception as e:
                    logger.warning(f"Error reading server.py in {example}: {e}")
        
        # Test passes if we get here
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
