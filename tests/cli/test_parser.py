#!/usr/bin/env python3
"""
Unit tests for the UnitMCP CLI Command Parser.

These tests verify that the command parser correctly parses and executes
commands for the UnitMCP CLI.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import argparse
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.cli.parser import CommandParser

class TestCommandParser(unittest.TestCase):
    """Test cases for the command parser."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mocks
        self.mock_host = 'test-host'
        self.mock_port = 9999
        self.mock_config = {
            'hardware_integration': MagicMock(),
            'claude_integration': MagicMock()
        }
        
        # Create the parser
        self.parser = CommandParser(
            host=self.mock_host,
            port=self.mock_port,
            config=self.mock_config
        )
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.parser.host, self.mock_host)
        self.assertEqual(self.parser.port, self.mock_port)
        self.assertEqual(self.parser.config, self.mock_config)
    
    @patch('unitmcp.cli.parser.CommandParser._handle_device_command')
    async def test_parse_and_execute_device_command(self, mock_handle_device_command):
        """Test parsing and executing a device command."""
        # Setup mock
        mock_handle_device_command.return_value = {'result': 'success'}
        
        # Parse and execute command
        args = ['device', 'control', 'test_led', 'activate']
        result = await self.parser.parse_and_execute(args)
        
        # Verify
        self.assertEqual(result, {'result': 'success'})
        mock_handle_device_command.assert_called_once()
    
    @patch('unitmcp.cli.parser.CommandParser._handle_automation_command')
    async def test_parse_and_execute_automation_command(self, mock_handle_automation_command):
        """Test parsing and executing an automation command."""
        # Setup mock
        mock_handle_automation_command.return_value = {'result': 'success'}
        
        # Parse and execute command
        args = ['automation', 'enable', 'test_automation']
        result = await self.parser.parse_and_execute(args)
        
        # Verify
        self.assertEqual(result, {'result': 'success'})
        mock_handle_automation_command.assert_called_once()
    
    @patch('unitmcp.cli.parser.CommandParser._handle_system_command')
    async def test_parse_and_execute_system_command(self, mock_handle_system_command):
        """Test parsing and executing a system command."""
        # Setup mock
        mock_handle_system_command.return_value = {'result': 'success'}
        
        # Parse and execute command
        args = ['system', 'status']
        result = await self.parser.parse_and_execute(args)
        
        # Verify
        self.assertEqual(result, {'result': 'success'})
        mock_handle_system_command.assert_called_once()
    
    @patch('unitmcp.cli.parser.CommandParser._handle_nl_command')
    async def test_parse_and_execute_nl_command(self, mock_handle_nl_command):
        """Test parsing and executing a natural language command."""
        # Setup mock
        mock_handle_nl_command.return_value = {'result': 'success'}
        
        # Parse and execute command
        args = ['nl', 'Turn', 'on', 'the', 'kitchen', 'light']
        result = await self.parser.parse_and_execute(args)
        
        # Verify
        self.assertEqual(result, {'result': 'success'})
        mock_handle_nl_command.assert_called_once()
    
    async def test_handle_device_command_list(self):
        """Test handling a device list command."""
        # Setup
        self.mock_config['hardware_integration'].get_devices.return_value = {
            'test_led': MagicMock(),
            'test_button': MagicMock()
        }
        
        # Create args
        args = argparse.Namespace()
        args.command = 'device'
        args.subcommand = 'list'
        
        # Handle command
        result = await self.parser._handle_device_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertEqual(len(result['devices']), 2)
        self.assertIn('test_led', result['devices'])
        self.assertIn('test_button', result['devices'])
        
        # Verify hardware integration was called
        self.mock_config['hardware_integration'].get_devices.assert_called_once()
    
    async def test_handle_device_command_info(self):
        """Test handling a device info command."""
        # Setup
        mock_device = MagicMock()
        mock_device.get_info.return_value = {'type': 'led', 'pin': 17}
        self.mock_config['hardware_integration'].get_device.return_value = mock_device
        
        # Create args
        args = argparse.Namespace()
        args.command = 'device'
        args.subcommand = 'info'
        args.device_id = 'test_led'
        
        # Handle command
        result = await self.parser._handle_device_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('device', result)
        self.assertEqual(result['device']['id'], 'test_led')
        self.assertEqual(result['device']['type'], 'led')
        self.assertEqual(result['device']['pin'], 17)
        
        # Verify hardware integration was called
        self.mock_config['hardware_integration'].get_device.assert_called_once_with('test_led')
    
    async def test_handle_device_command_control(self):
        """Test handling a device control command."""
        # Setup
        self.mock_config['hardware_integration'].execute_command.return_value = True
        
        # Create args
        args = argparse.Namespace()
        args.command = 'device'
        args.subcommand = 'control'
        args.device_id = 'test_led'
        args.action = 'activate'
        args.parameters = ['brightness=100', 'color=red']
        
        # Handle command
        result = await self.parser._handle_device_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        
        # Verify hardware integration was called
        self.mock_config['hardware_integration'].execute_command.assert_called_once_with(
            'test_led',
            'activate',
            brightness=100,
            color='red'
        )
    
    async def test_handle_device_command_unknown(self):
        """Test handling an unknown device command."""
        # Create args
        args = argparse.Namespace()
        args.command = 'device'
        args.subcommand = 'unknown'
        
        # Handle command
        result = await self.parser._handle_device_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
    
    async def test_handle_automation_command_list(self):
        """Test handling an automation list command."""
        # Setup
        self.mock_config['hardware_integration'].get_automations.return_value = {
            'test_automation': MagicMock()
        }
        
        # Create args
        args = argparse.Namespace()
        args.command = 'automation'
        args.subcommand = 'list'
        
        # Handle command
        result = await self.parser._handle_automation_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('automations', result)
        self.assertEqual(len(result['automations']), 1)
        self.assertIn('test_automation', result['automations'])
    
    async def test_handle_automation_command_enable(self):
        """Test handling an automation enable command."""
        # Setup
        self.mock_config['hardware_integration'].enable_automation.return_value = True
        
        # Create args
        args = argparse.Namespace()
        args.command = 'automation'
        args.subcommand = 'enable'
        args.automation_id = 'test_automation'
        
        # Handle command
        result = await self.parser._handle_automation_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        
        # Verify hardware integration was called
        self.mock_config['hardware_integration'].enable_automation.assert_called_once_with('test_automation')
    
    async def test_handle_automation_command_unknown(self):
        """Test handling an unknown automation command."""
        # Create args
        args = argparse.Namespace()
        args.command = 'automation'
        args.subcommand = 'unknown'
        
        # Handle command
        result = await self.parser._handle_automation_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
    
    async def test_handle_system_command_status(self):
        """Test handling a system status command."""
        # Setup
        self.mock_config['hardware_integration'].get_system_status.return_value = {
            'status': 'running',
            'devices': 2,
            'automations': 1
        }
        
        # Create args
        args = argparse.Namespace()
        args.command = 'system'
        args.subcommand = 'status'
        
        # Handle command
        result = await self.parser._handle_system_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'running')
        self.assertEqual(result['devices'], 2)
        self.assertEqual(result['automations'], 1)
    
    async def test_handle_system_command_unknown(self):
        """Test handling an unknown system command."""
        # Create args
        args = argparse.Namespace()
        args.command = 'system'
        args.subcommand = 'unknown'
        
        # Handle command
        result = await self.parser._handle_system_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
    
    async def test_handle_nl_command(self):
        """Test handling a natural language command."""
        # Setup
        self.mock_config['claude_integration'].process_command.return_value = {
            'command_type': 'device_control',
            'target': 'test_led',
            'action': 'activate',
            'parameters': {}
        }
        self.mock_config['hardware_integration'].execute_command.return_value = True
        
        # Create args
        args = argparse.Namespace()
        args.command = 'nl'
        args.command = ['Turn', 'on', 'the', 'test_led']
        
        # Handle command
        result = await self.parser._handle_nl_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('command', result)
        self.assertEqual(result['command']['command_type'], 'device_control')
        self.assertEqual(result['command']['target'], 'test_led')
        self.assertEqual(result['command']['action'], 'activate')
        
        # Verify Claude integration was called
        self.mock_config['claude_integration'].process_command.assert_called_once()
        
        # Verify hardware integration was called
        self.mock_config['hardware_integration'].execute_command.assert_called_once_with(
            'test_led',
            'activate'
        )
    
    async def test_handle_nl_command_error(self):
        """Test handling a natural language command with error."""
        # Setup
        self.mock_config['claude_integration'].process_command.return_value = {
            'error': 'Failed to parse command'
        }
        
        # Create args
        args = argparse.Namespace()
        args.command = 'nl'
        args.command = ['Invalid', 'command']
        
        # Handle command
        result = await self.parser._handle_nl_command(args)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        
        # Verify Claude integration was called
        self.mock_config['claude_integration'].process_command.assert_called_once()
        
        # Verify hardware integration was not called
        self.mock_config['hardware_integration'].execute_command.assert_not_called()

if __name__ == '__main__':
    unittest.main()
