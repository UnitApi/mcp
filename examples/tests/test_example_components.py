#!/usr/bin/env python3
"""
Test module for UnitMCP example components.
This module contains tests for the common components of UnitMCP examples.
"""

import os
import sys
import unittest
import yaml
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the base runner
from runner.base_runner import BaseRunner


class TestBaseRunner(unittest.TestCase):
    """Test the BaseRunner class."""

    def setUp(self):
        """Set up the test environment."""
        # Create temporary config files for testing
        self.temp_dir = os.path.dirname(__file__)
        self.server_config_path = os.path.join(self.temp_dir, "test_server_config.yaml")
        self.client_config_path = os.path.join(self.temp_dir, "test_client_config.yaml")
        
        # Create test config files
        with open(self.server_config_path, "w") as f:
            yaml.dump({"server": {"port": 8000}}, f)
        
        with open(self.client_config_path, "w") as f:
            yaml.dump({"connection": {"server_port": 8000}}, f)
        
        self.server_script_path = "server.py"
        self.client_script_path = "client.py"
        
        # Create the runner
        self.runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            server_script_path=self.server_script_path,
            client_script_path=self.client_script_path
        )

    def tearDown(self):
        """Clean up after tests."""
        # Remove test config files
        if os.path.exists(self.server_config_path):
            os.remove(self.server_config_path)
        
        if os.path.exists(self.client_config_path):
            os.remove(self.client_config_path)

    @patch('subprocess.Popen')
    def test_start_server(self, mock_popen):
        """Test the start_server method."""
        # Mock the subprocess.Popen call
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Call the start_server method
        result = self.runner.start_server()

        # Check that the server process was started
        self.assertTrue(result)
        self.assertEqual(self.runner.server_process, mock_process)
        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    def test_start_client(self, mock_popen):
        """Test the start_client method."""
        # Mock the subprocess.Popen call
        mock_process = MagicMock()
        mock_process.pid = 12346
        mock_popen.return_value = mock_process

        # Call the start_client method
        result = self.runner.start_client()

        # Check that the client process was started
        self.assertTrue(result)
        self.assertEqual(self.runner.client_process, mock_process)
        mock_popen.assert_called_once()

    @patch('signal.signal')
    @patch('time.sleep')
    @patch('subprocess.Popen')
    def test_run(self, mock_popen, mock_sleep, mock_signal):
        """Test the run method."""
        # Mock the subprocess.Popen call
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_server_process.poll.return_value = None  # Process is running
        
        mock_client_process = MagicMock()
        mock_client_process.pid = 12346
        mock_client_process.poll.return_value = None  # Process is running
        
        # Set up the mock to return different values on consecutive calls
        mock_popen.side_effect = [mock_server_process, mock_client_process]
        
        # Mock the running attribute to exit the loop after one iteration
        self.runner.running = True
        
        def set_running_false(*args, **kwargs):
            self.runner.running = False
        
        # Set the mock_sleep to set running to False
        mock_sleep.side_effect = set_running_false
        
        # Call the run method
        result = self.runner.run()
        
        # Check that the run method worked correctly
        self.assertEqual(result, 0)
        self.assertEqual(mock_popen.call_count, 2)
        self.assertEqual(mock_signal.call_count, 2)

    @patch('subprocess.Popen')
    def test_stop_processes(self, mock_popen):
        """Test the stop_processes method."""
        # Mock the subprocess.Popen call
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_server_process.poll.return_value = None  # Process is running
        
        mock_client_process = MagicMock()
        mock_client_process.pid = 12346
        mock_client_process.poll.return_value = None  # Process is running
        
        # Set up the processes
        self.runner.server_process = mock_server_process
        self.runner.client_process = mock_client_process
        
        # Call the stop_processes method
        result = self.runner.stop_processes()
        
        # Check that the processes were terminated
        self.assertTrue(result)
        mock_server_process.terminate.assert_called_once()
        mock_client_process.terminate.assert_called_once()

    def test_config_loading(self):
        """Test that configurations are loaded correctly."""
        # Check that the server config was loaded
        self.assertIsNotNone(self.runner.server_config)
        self.assertIn("server", self.runner.server_config)
        self.assertEqual(self.runner.server_config["server"]["port"], 8000)
        
        # Check that the client config was loaded
        self.assertIsNotNone(self.runner.client_config)
        self.assertIn("connection", self.runner.client_config)
        self.assertEqual(self.runner.client_config["connection"]["server_port"], 8000)


class TestExampleConfig(unittest.TestCase):
    """Test the example configuration files."""

    def test_server_config(self):
        """Test that the server config is valid."""
        # Find all server config files
        examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        for root, dirs, files in os.walk(examples_dir):
            if "config" in dirs:
                config_dir = os.path.join(root, "config")
                server_config_path = os.path.join(config_dir, "server.yaml")
                if os.path.exists(server_config_path):
                    with open(server_config_path, "r") as f:
                        config = yaml.safe_load(f)
                        # Check that the config has the required fields
                        self.assertIsNotNone(config, f"Server config is empty: {server_config_path}")
                        if "server" in config:
                            self.assertIn("port", config["server"], 
                                         f"Server config missing port: {server_config_path}")

    def test_client_config(self):
        """Test that the client config is valid."""
        # Find all client config files
        examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        for root, dirs, files in os.walk(examples_dir):
            if "config" in dirs:
                config_dir = os.path.join(root, "config")
                client_config_path = os.path.join(config_dir, "client.yaml")
                if os.path.exists(client_config_path):
                    with open(client_config_path, "r") as f:
                        config = yaml.safe_load(f)
                        # Check that the config has the required fields
                        self.assertIsNotNone(config, f"Client config is empty: {client_config_path}")
                        if "connection" in config:
                            self.assertIn("server_port", config["connection"], 
                                         f"Client config missing server_port: {client_config_path}")


if __name__ == "__main__":
    unittest.main()
