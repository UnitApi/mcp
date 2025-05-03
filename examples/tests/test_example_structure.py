#!/usr/bin/env python3
"""
Test module for UnitMCP example structure.
This module contains tests to verify that all examples follow the standardized structure.
"""

import os
import sys
import unittest
import importlib.util

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

    def test_example_structure(self):
        """Test that all examples have the required files."""
        for example in self.examples:
            with self.subTest(example=example):
                for required_file in self.required_files:
                    file_path = os.path.join(example, required_file)
                    self.assertTrue(os.path.exists(file_path), 
                                   f"Required file {required_file} missing in {example}")

    def test_runner_imports(self):
        """Test that all runner.py files import the BaseRunner."""
        for example in self.examples:
            runner_path = os.path.join(example, "runner.py")
            if os.path.exists(runner_path):
                with self.subTest(example=example):
                    # Check if the file imports BaseRunner
                    with open(runner_path, "r") as f:
                        content = f.read()
                        self.assertIn("BaseRunner", content, 
                                     f"Runner in {example} does not import BaseRunner")
                        self.assertIn("from runner.base_runner import", content, 
                                     f"Runner in {example} does not import from runner.base_runner")

    def test_runner_implementation(self):
        """Test that all runner.py files implement a Runner class."""
        for example in self.examples:
            runner_path = os.path.join(example, "runner.py")
            if os.path.exists(runner_path):
                with self.subTest(example=example):
                    # Try to import the Runner class from the module
                    try:
                        spec = importlib.util.spec_from_file_location("runner", runner_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Check if the module has a Runner class
                        self.assertTrue(hasattr(module, "Runner"), 
                                       f"Runner in {example} does not have a Runner class")
                        
                        # Check if the Runner class inherits from BaseRunner
                        runner_class = getattr(module, "Runner")
                        self.assertTrue("BaseRunner" in [base.__name__ for base in runner_class.__bases__], 
                                       f"Runner in {example} does not inherit from BaseRunner")
                    except Exception as e:
                        self.fail(f"Error importing Runner from {example}: {e}")

    def test_client_implementation(self):
        """Test that all client.py files implement required functions."""
        for example in self.examples:
            client_path = os.path.join(example, "client.py")
            if os.path.exists(client_path):
                with self.subTest(example=example):
                    # Check if the file has a main function
                    with open(client_path, "r") as f:
                        content = f.read()
                        self.assertIn("if __name__ == \"__main__\"", content, 
                                     f"Client in {example} does not have a main block")

    def test_server_implementation(self):
        """Test that all server.py files implement required functions."""
        for example in self.examples:
            server_path = os.path.join(example, "server.py")
            if os.path.exists(server_path):
                with self.subTest(example=example):
                    # Check if the file has a main function
                    with open(server_path, "r") as f:
                        content = f.read()
                        self.assertIn("if __name__ == \"__main__\"", content, 
                                     f"Server in {example} does not have a main block")


if __name__ == "__main__":
    unittest.main()
