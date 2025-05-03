#!/usr/bin/env python3
"""
UnitMCP Example Template - Tests

This module contains tests for the example template.
"""

import os
import sys
import unittest
import tempfile
import yaml
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the example components
from server import ExampleServer
from client import ExampleClient
from runner import ExampleRunner


class TestExampleServer(unittest.TestCase):
    """Test cases for the ExampleServer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create server config
        self.server_config = {
            'server': {
                'host': 'localhost',
                'port': 8000
            },
            'commands': {
                'allowed': ['status', 'help']
            }
        }
        self.server_config_path = os.path.join(self.temp_dir.name, 'server.yaml')
        with open(self.server_config_path, 'w') as f:
            yaml.dump(self.server_config, f)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of ExampleServer."""
        server = ExampleServer(self.server_config_path)
        
        self.assertEqual(server.config_path, self.server_config_path)
        self.assertEqual(server.host, 'localhost')
        self.assertEqual(server.port, 8000)
        self.assertFalse(server.running)
        self.assertIsNone(server.server)
        self.assertEqual(server.clients, set())

    def test_load_config(self):
        """Test loading configuration from a YAML file."""
        server = ExampleServer(self.server_config_path)
        config = server._load_config()
        
        self.assertEqual(config, self.server_config)
        
        # Test with invalid config path
        server.config_path = os.path.join(self.temp_dir.name, 'nonexistent.yaml')
        config = server._load_config()
        self.assertEqual(config, {})

    @patch('asyncio.start_server')
    async def test_start(self, mock_start_server):
        """Test starting the server."""
        # Mock the server
        mock_server = MagicMock()
        mock_start_server.return_value = mock_server
        
        server = ExampleServer(self.server_config_path)
        
        # Test successful start
        result = await server.start()
        
        self.assertTrue(result)
        self.assertTrue(server.running)
        self.assertEqual(server.server, mock_server)
        mock_start_server.assert_called_once_with(
            server.handle_client,
            server.host,
            server.port,
            limit=1024 * 1024
        )
        
        # Test exception handling
        mock_start_server.side_effect = Exception("Test exception")
        server.running = False
        server.server = None
        
        result = await server.start()
        
        self.assertFalse(result)
        self.assertFalse(server.running)
        self.assertIsNone(server.server)

    async def test_process_command(self):
        """Test processing a command."""
        server = ExampleServer(self.server_config_path)
        
        # Test status command
        command = {'type': 'status'}
        response = await server.process_command(command)
        
        self.assertEqual(response['status'], 'ok')
        self.assertEqual(response['message'], 'Server is running')
        self.assertIn('clients', response['data'])
        
        # Test help command
        command = {'type': 'help'}
        response = await server.process_command(command)
        
        self.assertEqual(response['status'], 'ok')
        self.assertEqual(response['message'], 'Available commands')
        self.assertIn('commands', response['data'])
        
        # Test unknown command
        command = {'type': 'unknown'}
        response = await server.process_command(command)
        
        self.assertEqual(response['status'], 'error')
        self.assertEqual(response['message'], 'Unknown command: unknown')


class TestExampleClient(unittest.TestCase):
    """Test cases for the ExampleClient class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create client config
        self.client_config = {
            'client': {
                'name': 'test-client',
                'id': 'test-001'
            },
            'connection': {
                'server_host': 'localhost',
                'server_port': 8000,
                'retry_attempts': 1
            }
        }
        self.client_config_path = os.path.join(self.temp_dir.name, 'client.yaml')
        with open(self.client_config_path, 'w') as f:
            yaml.dump(self.client_config, f)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of ExampleClient."""
        client = ExampleClient(self.client_config_path)
        
        self.assertEqual(client.config_path, self.client_config_path)
        self.assertEqual(client.name, 'test-client')
        self.assertEqual(client.client_id, 'test-001')
        self.assertEqual(client.server_host, 'localhost')
        self.assertEqual(client.server_port, 8000)
        self.assertEqual(client.retry_attempts, 1)
        self.assertFalse(client.running)
        self.assertIsNone(client.reader)
        self.assertIsNone(client.writer)

    def test_load_config(self):
        """Test loading configuration from a YAML file."""
        client = ExampleClient(self.client_config_path)
        config = client._load_config()
        
        self.assertEqual(config, self.client_config)
        
        # Test with invalid config path
        client.config_path = os.path.join(self.temp_dir.name, 'nonexistent.yaml')
        config = client._load_config()
        self.assertEqual(config, {})

    @patch('asyncio.open_connection')
    async def test_connect(self, mock_open_connection):
        """Test connecting to the server."""
        # Mock the connection
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        client = ExampleClient(self.client_config_path)
        
        # Test successful connection
        result = await client.connect()
        
        self.assertTrue(result)
        self.assertEqual(client.reader, mock_reader)
        self.assertEqual(client.writer, mock_writer)
        mock_open_connection.assert_called_once_with(
            client.server_host,
            client.server_port
        )
        
        # Test connection refused
        mock_open_connection.side_effect = ConnectionRefusedError("Connection refused")
        client.reader = None
        client.writer = None
        
        result = await client.connect()
        
        self.assertFalse(result)
        self.assertIsNone(client.reader)
        self.assertIsNone(client.writer)
        
        # Test other exception
        mock_open_connection.side_effect = Exception("Test exception")
        
        result = await client.connect()
        
        self.assertFalse(result)
        self.assertIsNone(client.reader)
        self.assertIsNone(client.writer)


class TestExampleRunner(unittest.TestCase):
    """Test cases for the ExampleRunner class."""

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
                'name': 'test-client',
                'id': 'test-001'
            },
            'connection': {
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
            f.write('#!/usr/bin/env python3\nprint("Server started")\n')
        
        with open(self.client_script_path, 'w') as f:
            f.write('#!/usr/bin/env python3\nprint("Client started")\n')
        
        # Make scripts executable
        os.chmod(self.server_script_path, 0o755)
        os.chmod(self.client_script_path, 0o755)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of ExampleRunner."""
        runner = ExampleRunner(
            server_config_path=self.server_config_path,
            client_config_path=self.client_config_path,
            server_script_path=self.server_script_path,
            client_script_path=self.client_script_path
        )
        
        self.assertEqual(runner.server_config_path, self.server_config_path)
        self.assertEqual(runner.client_config_path, self.client_config_path)
        self.assertEqual(runner.server_script_path, self.server_script_path)
        self.assertEqual(runner.client_script_path, self.client_script_path)
        
        # Test default paths
        runner = ExampleRunner()
        
        self.assertTrue(os.path.exists(os.path.dirname(runner.server_config_path)))
        self.assertTrue(os.path.exists(os.path.dirname(runner.client_config_path)))
        self.assertTrue(os.path.exists(os.path.dirname(runner.server_script_path)))
        self.assertTrue(os.path.exists(os.path.dirname(runner.client_script_path)))


if __name__ == '__main__':
    unittest.main()
