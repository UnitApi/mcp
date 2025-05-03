#!/usr/bin/env python3
"""
Tests for the UnitMCP Base Runner.

This module contains tests for the BaseRunner class to ensure
it correctly manages client-server processes.
"""

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the BaseRunner class
from base_runner import BaseRunner


class TestBaseRunner(unittest.TestCase):
    """Test cases for the BaseRunner class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create server config
        self.server_config = {
            'server': {
                'host': 'localhost',
                'port': 8000
            }
        }
        self.server_config_path = os.path.join(self.temp_dir.name, 'server.yaml')
        with open(self.server_config_path, 'w') as f:
            yaml.dump(self.server_config, f)
        
        # Create client config
        self.client_config = {
            'client': {
                'server_host': 'localhost',
                'server_port': 8000
            }
        }
        self.client_config_path = os.path.join(self.temp_dir.name, 'client.yaml')
        with open(self.client_config_path, 'w') as f:
            yaml.dump(self.client_config, f)
        
        # Create mock script paths
        self.server_script_path = os.path.join(self.temp_dir.name, 'server.py')
        self.client_script_path = os.path.join(self.temp_dir.name, 'client.py')
        
        # Create empty script files
        with open(self.server_script_path, 'w') as f:
            f.write('#!/usr/bin/env python3\nprint("Server started")\nimport time\nwhile True: time.sleep(1)\n')
        
        with open(self.client_script_path, 'w') as f:
            f.write('#!/usr/bin/env python3\nprint("Client started")\nimport time\nwhile True: time.sleep(1)\n')
        
        # Make scripts executable
        os.chmod(self.server_script_path, 0o755)
        os.chmod(self.client_script_path, 0o755)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of BaseRunner."""
        runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            server_script_path=self.server_script_path,
            client_script_path=self.client_script_path
        )
        
        self.assertEqual(runner.server_config_path, self.server_config_path)
        self.assertEqual(runner.client_config_path, self.client_config_path)
        self.assertEqual(runner.server_script_path, self.server_script_path)
        self.assertEqual(runner.client_script_path, self.client_script_path)
        self.assertEqual(runner.server_config, self.server_config)
        self.assertEqual(runner.client_config, self.client_config)
        self.assertFalse(runner.running)
        self.assertIsNone(runner.server_process)
        self.assertIsNone(runner.client_process)

    def test_load_config(self):
        """Test loading configuration from YAML files."""
        runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path
        )
        
        # Test valid config
        config = runner._load_config(self.server_config_path)
        self.assertEqual(config, self.server_config)
        
        # Test invalid config
        invalid_path = os.path.join(self.temp_dir.name, 'nonexistent.yaml')
        config = runner._load_config(invalid_path)
        self.assertEqual(config, {})

    @patch('subprocess.Popen')
    def test_start_server(self, mock_popen):
        """Test starting the server process."""
        # Mock the subprocess.Popen
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            server_script_path=self.server_script_path
        )
        
        result = runner.start_server()
        
        self.assertTrue(result)
        self.assertEqual(runner.server_process, mock_process)
        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    def test_start_client(self, mock_popen):
        """Test starting the client process."""
        # Mock the subprocess.Popen
        mock_process = MagicMock()
        mock_process.pid = 12346
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            client_script_path=self.client_script_path
        )
        
        result = runner.start_client()
        
        self.assertTrue(result)
        self.assertEqual(runner.client_process, mock_process)
        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    def test_stop_processes(self, mock_popen):
        """Test stopping processes."""
        # Mock the subprocess.Popen
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_server_process.poll.return_value = None
        
        mock_client_process = MagicMock()
        mock_client_process.pid = 12346
        mock_client_process.poll.return_value = None
        
        runner = BaseRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path
        )
        
        runner.server_process = mock_server_process
        runner.client_process = mock_client_process
        
        result = runner.stop_processes()
        
        self.assertTrue(result)
        mock_server_process.terminate.assert_called_once()
        mock_client_process.terminate.assert_called_once()

    @patch('time.sleep')
    @patch('subprocess.Popen')
    def test_run(self, mock_popen, mock_sleep):
        """Test running the example."""
        # Mock the subprocess.Popen
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_server_process.poll.side_effect = [None, None, 0]
        mock_server_process.stdout = MagicMock()
        mock_server_process.stderr = MagicMock()
        
        mock_client_process = MagicMock()
        mock_client_process.pid = 12346
        mock_client_process.poll.return_value = None
        mock_client_process.stdout = MagicMock()
        mock_client_process.stderr = MagicMock()
        
        mock_popen.side_effect = [mock_server_process, mock_client_process]
        
        # Mock the EnvLoader
        with patch('src.unitmcp.utils.env_loader.EnvLoader') as mock_env_loader:
            mock_env_loader_instance = MagicMock()
            mock_env_loader.return_value = mock_env_loader_instance
            
            runner = BaseRunner(
                server_config_path=self.server_config_path,
                client_config_path=self.client_config_path,
                server_script_path=self.server_script_path,
                client_script_path=self.client_script_path
            )
            
            result = runner.run()
            
            self.assertEqual(result, 0)
            mock_env_loader_instance.load_env.assert_called_once()
            mock_server_process.terminate.assert_called_once()
            mock_client_process.terminate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
