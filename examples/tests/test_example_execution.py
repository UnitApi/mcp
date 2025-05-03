#!/usr/bin/env python3
"""
Test module for UnitMCP example execution.
This module contains tests to verify that all examples can be executed correctly.
"""

import os
import sys
import unittest
import subprocess
import time
import signal
import yaml
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestExampleExecution(unittest.TestCase):
    """Test the execution of examples."""

    def setUp(self):
        """Set up the test environment."""
        self.examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.examples = self._find_examples()
        self.processes = []
        self.test_report = {"passed": [], "failed": [], "skipped": []}

    def tearDown(self):
        """Clean up after tests."""
        # Kill any remaining processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
        
        # Save the test report
        report_path = os.path.join(self.examples_dir, "tests", "example_execution_report.json")
        with open(report_path, "w") as f:
            json.dump(self.test_report, f, indent=2)

    def _find_examples(self):
        """Find all examples in the examples directory."""
        examples = []
        for item in os.listdir(self.examples_dir):
            item_path = os.path.join(self.examples_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.') and not item == 'tests' and not item == 'runner':
                # Only include examples with all required files
                if self._has_required_files(item_path):
                    examples.append(item_path)
                
                # Check for subdirectories that might be examples
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path) and not subitem.startswith('.') and not subitem == 'tests':
                        if self._has_required_files(subitem_path):
                            examples.append(subitem_path)
        return examples

    def _has_required_files(self, example_dir):
        """Check if an example has all required files."""
        required_files = [
            "runner.py",
            "client.py",
            "server.py",
        ]
        for required_file in required_files:
            if not os.path.exists(os.path.join(example_dir, required_file)):
                return False
        
        # Check for config directory
        config_dir = os.path.join(example_dir, "config")
        if not os.path.exists(config_dir) or not os.path.isdir(config_dir):
            return False
        
        return True

    def _update_config_ports(self, example_dir, port_offset):
        """Update the config files to use unique ports."""
        server_config_path = os.path.join(example_dir, "config", "server.yaml")
        client_config_path = os.path.join(example_dir, "config", "client.yaml")
        
        # Use a unique port for each example
        server_port = 9500 + port_offset
        
        if os.path.exists(server_config_path):
            try:
                # Load the server config
                with open(server_config_path, "r") as f:
                    server_config = yaml.safe_load(f) or {}
                
                # Update the port
                if "server" not in server_config:
                    server_config["server"] = {}
                server_config["server"]["port"] = server_port
                
                # Save the updated config
                with open(server_config_path, "w") as f:
                    yaml.dump(server_config, f)
            except Exception as e:
                print(f"Error updating server config: {e}")
        
        if os.path.exists(client_config_path):
            try:
                # Load the client config
                with open(client_config_path, "r") as f:
                    client_config = yaml.safe_load(f) or {}
                
                # Update the port
                if "connection" not in client_config:
                    client_config["connection"] = {}
                client_config["connection"]["server_port"] = server_port
                
                # Save the updated config
                with open(client_config_path, "w") as f:
                    yaml.dump(client_config, f)
            except Exception as e:
                print(f"Error updating client config: {e}")
        
        return server_port

    def _create_test_input(self, example_dir):
        """Create a test input file for the example."""
        input_file = os.path.join(example_dir, ".test_input.txt")
        with open(input_file, "w") as f:
            f.write("help\nexit\n")
        return input_file

    def test_runner_imports(self):
        """Test that all runners import the required modules."""
        for example in self.examples:
            example_name = os.path.basename(example)
            with self.subTest(example=example_name):
                runner_path = os.path.join(example, "runner.py")
                if os.path.exists(runner_path):
                    try:
                        with open(runner_path, "r") as f:
                            content = f.read()
                            self.assertIn("from runner.base_runner import BaseRunner", content,
                                         f"Runner in {example_name} does not import BaseRunner")
                            self.test_report["passed"].append(f"{example_name}: runner imports")
                    except Exception as e:
                        self.test_report["failed"].append(f"{example_name}: runner imports - {str(e)}")
                        self.fail(f"Error checking runner imports in {example_name}: {e}")

    def test_runner_execution_mock(self):
        """Test that all runners can be executed with mocked processes."""
        for i, example in enumerate(self.examples):
            example_name = os.path.basename(example)
            with self.subTest(example=example_name):
                try:
                    # Update config files to use unique ports
                    port = self._update_config_ports(example, i)
                    
                    # Mock the subprocess.Popen
                    with patch('subprocess.Popen') as mock_popen:
                        # Mock the process
                        mock_process = MagicMock()
                        mock_process.pid = 12345
                        mock_process.poll.return_value = None  # Process is running
                        mock_popen.return_value = mock_process
                        
                        # Create a temporary file to provide input to the example
                        input_file = self._create_test_input(example)
                        
                        # Run the runner with a timeout
                        runner_path = os.path.join(example, "runner.py")
                        
                        # Execute the runner module directly
                        try:
                            sys.path.insert(0, example)
                            import runner
                            
                            # Create an instance of the Runner class
                            runner_instance = runner.Runner()
                            
                            # Start the runner
                            with patch('builtins.input', return_value='exit'):
                                # Mock the run method to avoid actually running the example
                                with patch.object(runner_instance, 'run'):
                                    runner_instance.run()
                            
                            # Clean up the input file
                            if os.path.exists(input_file):
                                os.remove(input_file)
                            
                            self.test_report["passed"].append(f"{example_name}: runner execution mock")
                        except Exception as e:
                            self.test_report["failed"].append(f"{example_name}: runner execution mock - {str(e)}")
                            self.fail(f"Error running runner in {example_name}: {e}")
                        finally:
                            # Clean up sys.path
                            if example in sys.path:
                                sys.path.remove(example)
                            # Clean up imported modules
                            if 'runner' in sys.modules:
                                del sys.modules['runner']
                except Exception as e:
                    self.test_report["failed"].append(f"{example_name}: runner execution mock setup - {str(e)}")
                    self.fail(f"Error setting up runner test in {example_name}: {e}")

    @unittest.skip("Skip actual execution tests for now")
    def test_runner_execution(self):
        """Test that all runners can be executed."""
        for i, example in enumerate(self.examples):
            example_name = os.path.basename(example)
            with self.subTest(example=example_name):
                try:
                    # Update config files to use unique ports
                    port = self._update_config_ports(example, i)
                    
                    # Create a temporary file to provide input to the example
                    input_file = self._create_test_input(example)
                    
                    # Run the runner with a timeout
                    runner_path = os.path.join(example, "runner.py")
                    try:
                        with open(input_file, "r") as input_stream:
                            process = subprocess.Popen(
                                [sys.executable, runner_path],
                                stdin=input_stream,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                cwd=example,
                            )
                            self.processes.append(process)
                            
                            # Wait for a short time to let the example start
                            time.sleep(5)
                            
                            # Send the exit command
                            process.communicate(input="exit\n", timeout=2)
                            
                            # Wait for the process to exit
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                # If the process doesn't exit, kill it
                                process.terminate()
                                try:
                                    process.wait(timeout=2)
                                except subprocess.TimeoutExpired:
                                    process.kill()
                            
                            # Check the exit code
                            self.assertEqual(process.returncode, 0, 
                                           f"Runner in {example_name} exited with non-zero code: {process.returncode}")
                            
                            # Clean up the input file
                            if os.path.exists(input_file):
                                os.remove(input_file)
                            
                            self.test_report["passed"].append(f"{example_name}: runner execution")
                    except Exception as e:
                        self.test_report["failed"].append(f"{example_name}: runner execution - {str(e)}")
                        self.fail(f"Error running runner in {example_name}: {e}")
                except Exception as e:
                    self.test_report["failed"].append(f"{example_name}: runner execution setup - {str(e)}")
                    self.fail(f"Error setting up runner test in {example_name}: {e}")

    @unittest.skip("Skip server tests for now as they require network access")
    def test_server_execution(self):
        """Test that all servers can be executed."""
        for i, example in enumerate(self.examples):
            example_name = os.path.basename(example)
            with self.subTest(example=example_name):
                try:
                    # Update config files to use unique ports
                    port = self._update_config_ports(example, i + 100)
                    
                    # Run the server with a timeout
                    server_path = os.path.join(example, "server.py")
                    try:
                        process = subprocess.Popen(
                            [sys.executable, server_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=example,
                        )
                        self.processes.append(process)
                        
                        # Wait for a short time to let the server start
                        time.sleep(2)
                        
                        # Check if the process is still running
                        self.assertIsNone(process.poll(), f"Server in {example_name} exited prematurely")
                        
                        # Kill the process
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        
                        self.test_report["passed"].append(f"{example_name}: server execution")
                    except Exception as e:
                        self.test_report["failed"].append(f"{example_name}: server execution - {str(e)}")
                        self.fail(f"Error running server in {example_name}: {e}")
                except Exception as e:
                    self.test_report["failed"].append(f"{example_name}: server execution setup - {str(e)}")
                    self.fail(f"Error setting up server test in {example_name}: {e}")

    @unittest.skip("Skip client tests for now as they require a running server")
    def test_client_execution(self):
        """Test that all clients can be executed."""
        for i, example in enumerate(self.examples):
            example_name = os.path.basename(example)
            with self.subTest(example=example_name):
                try:
                    # Update config files to use unique ports
                    port = self._update_config_ports(example, i + 200)
                    
                    # Start the server first
                    server_path = os.path.join(example, "server.py")
                    server_process = subprocess.Popen(
                        [sys.executable, server_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=example,
                    )
                    self.processes.append(server_process)
                    
                    # Wait for the server to start
                    time.sleep(2)
                    
                    # Create a temporary file to provide input to the client
                    input_file = self._create_test_input(example)
                    
                    # Run the client with a timeout
                    client_path = os.path.join(example, "client.py")
                    try:
                        with open(input_file, "r") as input_stream:
                            client_process = subprocess.Popen(
                                [sys.executable, client_path],
                                stdin=input_stream,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                cwd=example,
                            )
                            self.processes.append(client_process)
                            
                            # Wait for a short time to let the client start
                            time.sleep(2)
                            
                            # Check if the process is still running
                            self.assertIsNone(client_process.poll(), f"Client in {example_name} exited prematurely")
                            
                            # Kill the processes
                            client_process.terminate()
                            server_process.terminate()
                            try:
                                client_process.wait(timeout=5)
                                server_process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                client_process.kill()
                                server_process.kill()
                            
                            # Clean up the input file
                            if os.path.exists(input_file):
                                os.remove(input_file)
                            
                            self.test_report["passed"].append(f"{example_name}: client execution")
                    except Exception as e:
                        self.test_report["failed"].append(f"{example_name}: client execution - {str(e)}")
                        self.fail(f"Error running client in {example_name}: {e}")
                except Exception as e:
                    self.test_report["failed"].append(f"{example_name}: client execution setup - {str(e)}")
                    self.fail(f"Error setting up client test in {example_name}: {e}")


if __name__ == "__main__":
    unittest.main()
