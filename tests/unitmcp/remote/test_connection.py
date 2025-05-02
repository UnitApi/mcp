#!/usr/bin/env python3
"""
Unit tests for the remote connection module.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.remote.connection import (
    RemoteConnection, 
    SSHConnection, 
    MQTTConnection
)

class TestRemoteConnection(unittest.TestCase):
    """Test cases for the RemoteConnection base class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        connection = RemoteConnection()
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(connection.connect())
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(connection.disconnect())
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(connection.execute_command("test"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(connection.upload_file("source", "dest"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(connection.download_file("source", "dest"))


class TestSSHConnection(unittest.TestCase):
    """Test cases for the SSHConnection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = SSHConnection(
            host="test-host",
            port=22,
            username="test-user",
            password="test-password"
        )
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_connect(self, mock_connect):
        """Test connecting to an SSH server."""
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        result = await self.connection.connect()
        
        # Check that the connection was successful
        self.assertTrue(result)
        self.assertEqual(self.connection._client, mock_connection)
        
        # Check that the connect method was called with the correct arguments
        mock_connect.assert_called_once_with(
            host="test-host",
            port=22,
            username="test-user",
            password="test-password",
            known_hosts=None
        )
    
    def test_connect(self):
        """Test connecting to an SSH server (synchronous wrapper)."""
        asyncio.run(self.async_test_connect())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_connect_with_key(self, mock_connect):
        """Test connecting to an SSH server with a key file."""
        # Create a connection with a key file
        connection = SSHConnection(
            host="test-host",
            port=22,
            username="test-user",
            key_file="test-key.pem"
        )
        
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        result = await connection.connect()
        
        # Check that the connection was successful
        self.assertTrue(result)
        self.assertEqual(connection._client, mock_connection)
        
        # Check that the connect method was called with the correct arguments
        mock_connect.assert_called_once()
        args, kwargs = mock_connect.call_args
        self.assertEqual(kwargs["host"], "test-host")
        self.assertEqual(kwargs["port"], 22)
        self.assertEqual(kwargs["username"], "test-user")
        self.assertIn("client_keys", kwargs)
    
    def test_connect_with_key(self):
        """Test connecting to an SSH server with a key file (synchronous wrapper)."""
        asyncio.run(self.async_test_connect_with_key())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_connect_failure(self, mock_connect):
        """Test handling connection failures."""
        # Mock the SSH connection to raise an exception
        mock_connect.side_effect = Exception("Connection failed")
        
        # Try to connect to the server
        result = await self.connection.connect()
        
        # Check that the connection failed
        self.assertFalse(result)
        self.assertIsNone(self.connection._client)
    
    def test_connect_failure(self):
        """Test handling connection failures (synchronous wrapper)."""
        asyncio.run(self.async_test_connect_failure())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_disconnect(self, mock_connect):
        """Test disconnecting from an SSH server."""
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        await self.connection.connect()
        
        # Disconnect from the server
        result = await self.connection.disconnect()
        
        # Check that the disconnection was successful
        self.assertTrue(result)
        self.assertIsNone(self.connection._client)
        
        # Check that the close method was called
        mock_connection.close.assert_called_once()
    
    def test_disconnect(self):
        """Test disconnecting from an SSH server (synchronous wrapper)."""
        asyncio.run(self.async_test_disconnect())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_execute_command(self, mock_connect):
        """Test executing a command on an SSH server."""
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_process = AsyncMock()
        mock_process.stdout = "Command output"
        mock_process.stderr = "Command error"
        mock_process.exit_status = 0
        mock_connection.run.return_value = mock_process
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        await self.connection.connect()
        
        # Execute a command
        returncode, stdout, stderr = await self.connection.execute_command("test command")
        
        # Check that the command was executed correctly
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "Command output")
        self.assertEqual(stderr, "Command error")
        
        # Check that the run method was called with the correct arguments
        mock_connection.run.assert_called_once_with("test command")
    
    def test_execute_command(self):
        """Test executing a command on an SSH server (synchronous wrapper)."""
        asyncio.run(self.async_test_execute_command())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_upload_file(self, mock_connect):
        """Test uploading a file to an SSH server."""
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_sftp = AsyncMock()
        mock_connection.start_sftp_client.return_value = mock_sftp
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        await self.connection.connect()
        
        # Upload a file
        result = await self.connection.upload_file("local_file", "remote_file")
        
        # Check that the upload was successful
        self.assertTrue(result)
        
        # Check that the put method was called with the correct arguments
        mock_sftp.put.assert_called_once_with("local_file", "remote_file")
    
    def test_upload_file(self):
        """Test uploading a file to an SSH server (synchronous wrapper)."""
        asyncio.run(self.async_test_upload_file())
    
    @patch('unitmcp.remote.connection.asyncssh.connect')
    async def async_test_download_file(self, mock_connect):
        """Test downloading a file from an SSH server."""
        # Mock the SSH connection
        mock_connection = AsyncMock()
        mock_sftp = AsyncMock()
        mock_connection.start_sftp_client.return_value = mock_sftp
        mock_connect.return_value = mock_connection
        
        # Connect to the server
        await self.connection.connect()
        
        # Download a file
        result = await self.connection.download_file("remote_file", "local_file")
        
        # Check that the download was successful
        self.assertTrue(result)
        
        # Check that the get method was called with the correct arguments
        mock_sftp.get.assert_called_once_with("remote_file", "local_file")
    
    def test_download_file(self):
        """Test downloading a file from an SSH server (synchronous wrapper)."""
        asyncio.run(self.async_test_download_file())


class TestMQTTConnection(unittest.TestCase):
    """Test cases for the MQTTConnection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = MQTTConnection(
            host="test-host",
            port=1883,
            client_id="test-client"
        )
    
    @patch('unitmcp.remote.connection.mqtt.Client')
    async def async_test_connect(self, mock_client_class):
        """Test connecting to an MQTT broker."""
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Connect to the broker
        result = await self.connection.connect()
        
        # Check that the connection was successful
        self.assertTrue(result)
        self.assertEqual(self.connection._client, mock_client)
        
        # Check that the connect method was called with the correct arguments
        mock_client.connect.assert_called_once_with("test-host", 1883)
        mock_client.loop_start.assert_called_once()
    
    def test_connect(self):
        """Test connecting to an MQTT broker (synchronous wrapper)."""
        asyncio.run(self.async_test_connect())
    
    @patch('unitmcp.remote.connection.mqtt.Client')
    async def async_test_connect_with_auth(self, mock_client_class):
        """Test connecting to an MQTT broker with authentication."""
        # Create a connection with authentication
        connection = MQTTConnection(
            host="test-host",
            port=1883,
            client_id="test-client",
            username="test-user",
            password="test-password"
        )
        
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Connect to the broker
        result = await connection.connect()
        
        # Check that the connection was successful
        self.assertTrue(result)
        self.assertEqual(connection._client, mock_client)
        
        # Check that the username_pw_set method was called with the correct arguments
        mock_client.username_pw_set.assert_called_once_with("test-user", "test-password")
    
    def test_connect_with_auth(self):
        """Test connecting to an MQTT broker with authentication (synchronous wrapper)."""
        asyncio.run(self.async_test_connect_with_auth())
    
    @patch('unitmcp.remote.connection.mqtt.Client')
    async def async_test_disconnect(self, mock_client_class):
        """Test disconnecting from an MQTT broker."""
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Connect to the broker
        await self.connection.connect()
        
        # Disconnect from the broker
        result = await self.connection.disconnect()
        
        # Check that the disconnection was successful
        self.assertTrue(result)
        self.assertIsNone(self.connection._client)
        
        # Check that the disconnect and loop_stop methods were called
        mock_client.disconnect.assert_called_once()
        mock_client.loop_stop.assert_called_once()
    
    def test_disconnect(self):
        """Test disconnecting from an MQTT broker (synchronous wrapper)."""
        asyncio.run(self.async_test_disconnect())


if __name__ == '__main__':
    unittest.main()
