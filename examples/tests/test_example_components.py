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
        self.server_config_path = "config/server.yaml"
        self.client_config_path = "config/client.yaml"
        self.server_script_path = "server.py"
        self.client_script_path = "client.py"
        self.runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            server_script_path=self.server_script_path,
            client_script_path=self.client_script_path
        )

    @patch('subprocess.Popen')
    def test_start_server(self, mock_popen):
        """Test the start_server method."""
        # Mock the subprocess.Popen call
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Call the start_server method
        self.runner.start_server()

        # Check that the server process was started
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
        self.runner.start_client()

        # Check that the client process was started
        self.assertEqual(self.runner.client_process, mock_process)
        mock_popen.assert_called_once()

    @patch('signal.signal')
    def test_setup_signal_handlers(self, mock_signal):
        """Test the setup_signal_handlers method."""
        # Call the setup_signal_handlers method
        self.runner.setup_signal_handlers()

        # Check that signal.signal was called twice (for SIGINT and SIGTERM)
        self.assertEqual(mock_signal.call_count, 2)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"server": {"port": 8000}}')
    def test_load_config(self, mock_open, mock_exists):
        """Test the load_config method."""
        # Mock os.path.exists to return True
        mock_exists.return_value = True

        # Call the load_config method
        config = self.runner.load_config("config.yaml")

        # Check that the config was loaded correctly
        self.assertEqual(config, {"server": {"port": 8000}})
        mock_open.assert_called_once_with("config.yaml", "r")

    def test_validate_config(self):
        """Test the validate_config method."""
        # Test with a valid config
        valid_config = {"server": {"port": 8000}}
        self.assertTrue(self.runner.validate_config(valid_config, ["server"]))

        # Test with an invalid config
        invalid_config = {"client": {"port": 8000}}
        self.assertFalse(self.runner.validate_config(invalid_config, ["server"]))

    @patch('time.sleep')
    def test_wait_for_server(self, mock_sleep):
        """Test the wait_for_server method."""
        # Call the wait_for_server method
        self.runner.wait_for_server()

        # Check that time.sleep was called
        mock_sleep.assert_called_once_with(2)

    @patch('subprocess.Popen')
    def test_stop_processes(self, mock_popen):
        """Test the stop_processes method."""
        # Mock the subprocess.Popen call
        mock_server_process = MagicMock()
        mock_client_process = MagicMock()
        self.runner.server_process = mock_server_process
        self.runner.client_process = mock_client_process

        # Call the stop_processes method
        self.runner.stop_processes()

        # Check that the processes were terminated
        mock_server_process.terminate.assert_called_once()
        mock_client_process.terminate.assert_called_once()
        self.assertIsNone(self.runner.server_process)
        self.assertIsNone(self.runner.client_process)


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
