#!/usr/bin/env python3
"""
Unit tests for the UnitMCP DSL Hardware Integration.

These tests verify that the DSL hardware integration correctly loads
configurations and manages devices.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open
import yaml
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.integration import DslHardwareIntegration

class TestDslHardwareIntegration(unittest.TestCase):
    """Test cases for the DSL hardware integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create the integration
        self.integration = DslHardwareIntegration()
        
        # Test data
        self.test_config = {
            'unitmcp': {
                'name': 'test-controller',
                'platform': 'simulation',
                'mode': 'simulation'
            },
            'devices': {
                'test_led': {
                    'type': 'led',
                    'pin': 17,
                    'initial_state': 'off'
                },
                'test_button': {
                    'type': 'button',
                    'pin': 27,
                    'pull_up': True
                }
            },
            'automations': {
                'test_automation': {
                    'trigger': {
                        'platform': 'state',
                        'entity_id': 'test_button',
                        'to': 'on'
                    },
                    'action': {
                        'service': 'activate',
                        'entity_id': 'test_led'
                    }
                }
            }
        }
        
        self.yaml_config = yaml.dump(self.test_config)
    
    @patch('unitmcp.dsl.integration.DslCompiler')
    @patch('unitmcp.dsl.integration.DeviceConverter')
    def test_load_config(self, mock_converter, mock_compiler):
        """Test loading configuration."""
        # Setup mocks
        mock_compiler_instance = MagicMock()
        mock_compiler.return_value = mock_compiler_instance
        mock_compiler_instance.compile.return_value = self.test_config
        
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        # Create mock devices
        mock_led = MagicMock()
        mock_button = MagicMock()
        
        # Configure converter to return mock devices
        mock_converter_instance.convert.side_effect = lambda device_id, config: {
            'test_led': mock_led,
            'test_button': mock_button
        }.get(device_id)
        
        # Load configuration
        result = self.integration.load_config(self.yaml_config)
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertEqual(len(result['devices']), 2)
        self.assertIn('test_led', result['devices'])
        self.assertIn('test_button', result['devices'])
        
        # Verify compiler was called
        mock_compiler_instance.compile.assert_called_once_with(self.yaml_config)
        
        # Verify converter was called for each device
        self.assertEqual(mock_converter_instance.convert.call_count, 2)
        
        # Verify devices were stored
        self.assertEqual(len(self.integration._devices), 2)
        self.assertIn('test_led', self.integration._devices)
        self.assertIn('test_button', self.integration._devices)
        self.assertEqual(self.integration._devices['test_led'], mock_led)
        self.assertEqual(self.integration._devices['test_button'], mock_button)
    
    @patch('unitmcp.dsl.integration.DslCompiler')
    @patch('unitmcp.dsl.integration.DeviceConverter')
    def test_load_config_file(self, mock_converter, mock_compiler):
        """Test loading configuration from file."""
        # Setup mocks
        mock_compiler_instance = MagicMock()
        mock_compiler.return_value = mock_compiler_instance
        mock_compiler_instance.compile.return_value = self.test_config
        
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        # Create mock devices
        mock_led = MagicMock()
        mock_button = MagicMock()
        
        # Configure converter to return mock devices
        mock_converter_instance.convert.side_effect = lambda device_id, config: {
            'test_led': mock_led,
            'test_button': mock_button
        }.get(device_id)
        
        # Mock file open
        m = mock_open(read_data=self.yaml_config)
        with patch('builtins.open', m):
            # Load configuration from file
            result = self.integration.load_config_file('test_config.yaml')
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertEqual(len(result['devices']), 2)
        self.assertIn('test_led', result['devices'])
        self.assertIn('test_button', result['devices'])
        
        # Verify compiler was called
        mock_compiler_instance.compile.assert_called_once_with(self.yaml_config)
        
        # Verify converter was called for each device
        self.assertEqual(mock_converter_instance.convert.call_count, 2)
        
        # Verify devices were stored
        self.assertEqual(len(self.integration._devices), 2)
        self.assertIn('test_led', self.integration._devices)
        self.assertIn('test_button', self.integration._devices)
        self.assertEqual(self.integration._devices['test_led'], mock_led)
        self.assertEqual(self.integration._devices['test_button'], mock_button)
    
    def test_get_device(self):
        """Test getting a device."""
        # Setup
        mock_device = MagicMock()
        self.integration._devices = {'test_device': mock_device}
        
        # Get device
        device = self.integration.get_device('test_device')
        
        # Verify
        self.assertEqual(device, mock_device)
    
    def test_get_device_not_found(self):
        """Test getting a device that doesn't exist."""
        with self.assertRaises(KeyError):
            self.integration.get_device('non_existent_device')
    
    def test_get_devices(self):
        """Test getting all devices."""
        # Setup
        mock_device1 = MagicMock()
        mock_device2 = MagicMock()
        self.integration._devices = {
            'test_device1': mock_device1,
            'test_device2': mock_device2
        }
        
        # Get devices
        devices = self.integration.get_devices()
        
        # Verify
        self.assertEqual(len(devices), 2)
        self.assertIn('test_device1', devices)
        self.assertIn('test_device2', devices)
        self.assertEqual(devices['test_device1'], mock_device1)
        self.assertEqual(devices['test_device2'], mock_device2)
    
    def test_initialize_devices(self):
        """Test initializing devices."""
        # Setup
        mock_device1 = MagicMock()
        mock_device1.initialize = MagicMock(return_value=True)
        
        mock_device2 = MagicMock()
        mock_device2.initialize = MagicMock(return_value=True)
        
        self.integration._devices = {
            'test_device1': mock_device1,
            'test_device2': mock_device2
        }
        
        # Initialize devices
        result = self.integration.initialize_devices()
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn('test_device1', result)
        self.assertIn('test_device2', result)
        self.assertTrue(result['test_device1'])
        self.assertTrue(result['test_device2'])
        
        # Verify initialize was called for each device
        mock_device1.initialize.assert_called_once()
        mock_device2.initialize.assert_called_once()
    
    def test_cleanup_devices(self):
        """Test cleaning up devices."""
        # Setup
        mock_device1 = MagicMock()
        mock_device1.cleanup = MagicMock(return_value=True)
        
        mock_device2 = MagicMock()
        mock_device2.cleanup = MagicMock(return_value=True)
        
        self.integration._devices = {
            'test_device1': mock_device1,
            'test_device2': mock_device2
        }
        
        # Cleanup devices
        result = self.integration.cleanup_devices()
        
        # Verify
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn('test_device1', result)
        self.assertIn('test_device2', result)
        self.assertTrue(result['test_device1'])
        self.assertTrue(result['test_device2'])
        
        # Verify cleanup was called for each device
        mock_device1.cleanup.assert_called_once()
        mock_device2.cleanup.assert_called_once()
    
    def test_execute_command(self):
        """Test executing a command."""
        # Setup
        mock_device = MagicMock()
        mock_device.test_action = MagicMock(return_value=True)
        
        self.integration._devices = {'test_device': mock_device}
        
        # Execute command
        result = self.integration.execute_command('test_device', 'test_action', param1='value1')
        
        # Verify
        self.assertTrue(result)
        mock_device.test_action.assert_called_once_with(param1='value1')
    
    def test_execute_command_device_not_found(self):
        """Test executing a command for a device that doesn't exist."""
        with self.assertRaises(KeyError):
            self.integration.execute_command('non_existent_device', 'test_action')
    
    def test_execute_command_action_not_found(self):
        """Test executing a command for an action that doesn't exist."""
        # Setup
        mock_device = MagicMock()
        # No test_action method
        
        self.integration._devices = {'test_device': mock_device}
        
        # Execute command
        with self.assertRaises(AttributeError):
            self.integration.execute_command('test_device', 'test_action')

if __name__ == '__main__':
    unittest.main()
