#!/usr/bin/env python3
"""
Unit tests for the UnitMCP Device Converter.

These tests verify that the device converter correctly converts
DSL device configurations into UnitMCP device objects.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.converters.to_devices import DeviceConverter

class TestDeviceConverter(unittest.TestCase):
    """Test cases for the device converter."""
    
    def setUp(self):
        """Set up the test environment."""
        self.converter = DeviceConverter()
        
        # Test data
        self.led_config = {
            'type': 'led',
            'pin': 17,
            'initial_state': 'off'
        }
        
        self.button_config = {
            'type': 'button',
            'pin': 27,
            'pull_up': True
        }
        
        self.traffic_light_config = {
            'type': 'traffic_light',
            'red_pin': 22,
            'yellow_pin': 23,
            'green_pin': 24
        }
        
        self.display_config = {
            'type': 'display',
            'display_type': 'lcd',
            'width': 16,
            'height': 2
        }
    
    @patch('unitmcp.hardware.device_factory.LEDDevice')
    def test_convert_led(self, mock_led_device):
        """Test converting LED device configuration."""
        # Setup mock
        mock_instance = MagicMock()
        mock_led_device.return_value = mock_instance
        
        # Convert device
        device = self.converter.convert('test_led', self.led_config)
        
        # Verify
        self.assertEqual(device, mock_instance)
        mock_led_device.assert_called_once_with(
            device_id='test_led',
            pin=17,
            initial_state='off'
        )
    
    @patch('unitmcp.hardware.device_factory.ButtonDevice')
    def test_convert_button(self, mock_button_device):
        """Test converting button device configuration."""
        # Setup mock
        mock_instance = MagicMock()
        mock_button_device.return_value = mock_instance
        
        # Convert device
        device = self.converter.convert('test_button', self.button_config)
        
        # Verify
        self.assertEqual(device, mock_instance)
        mock_button_device.assert_called_once_with(
            device_id='test_button',
            pin=27,
            pull_up=True
        )
    
    @patch('unitmcp.hardware.device_factory.TrafficLightDevice')
    def test_convert_traffic_light(self, mock_traffic_light_device):
        """Test converting traffic light device configuration."""
        # Setup mock
        mock_instance = MagicMock()
        mock_traffic_light_device.return_value = mock_instance
        
        # Convert device
        device = self.converter.convert('test_traffic_light', self.traffic_light_config)
        
        # Verify
        self.assertEqual(device, mock_instance)
        mock_traffic_light_device.assert_called_once_with(
            device_id='test_traffic_light',
            red_pin=22,
            yellow_pin=23,
            green_pin=24
        )
    
    @patch('unitmcp.hardware.device_factory.DisplayDevice')
    def test_convert_display(self, mock_display_device):
        """Test converting display device configuration."""
        # Setup mock
        mock_instance = MagicMock()
        mock_display_device.return_value = mock_instance
        
        # Convert device
        device = self.converter.convert('test_display', self.display_config)
        
        # Verify
        self.assertEqual(device, mock_instance)
        mock_display_device.assert_called_once_with(
            device_id='test_display',
            display_type='lcd',
            width=16,
            height=2
        )
    
    def test_convert_unknown_type(self):
        """Test converting unknown device type."""
        config = {
            'type': 'unknown',
            'pin': 17
        }
        
        with self.assertRaises(ValueError):
            self.converter.convert('test_unknown', config)
    
    def test_convert_missing_required_param(self):
        """Test converting device with missing required parameter."""
        config = {
            'type': 'led'
            # Missing required pin
        }
        
        with self.assertRaises(ValueError):
            self.converter.convert('test_led', config)
    
    def test_get_device_class(self):
        """Test getting device class."""
        # LED
        device_class = self.converter._get_device_class('led')
        self.assertEqual(device_class.__name__, 'LEDDevice')
        
        # Button
        device_class = self.converter._get_device_class('button')
        self.assertEqual(device_class.__name__, 'ButtonDevice')
        
        # Traffic light
        device_class = self.converter._get_device_class('traffic_light')
        self.assertEqual(device_class.__name__, 'TrafficLightDevice')
        
        # Display
        device_class = self.converter._get_device_class('display')
        self.assertEqual(device_class.__name__, 'DisplayDevice')
        
        # Unknown
        with self.assertRaises(ValueError):
            self.converter._get_device_class('unknown')
    
    def test_get_required_params(self):
        """Test getting required parameters for device type."""
        # LED
        required_params = self.converter._get_required_params('led')
        self.assertIn('pin', required_params)
        
        # Button
        required_params = self.converter._get_required_params('button')
        self.assertIn('pin', required_params)
        
        # Traffic light
        required_params = self.converter._get_required_params('traffic_light')
        self.assertIn('red_pin', required_params)
        self.assertIn('yellow_pin', required_params)
        self.assertIn('green_pin', required_params)
        
        # Display
        required_params = self.converter._get_required_params('display')
        self.assertIn('display_type', required_params)
        
        # Unknown
        with self.assertRaises(ValueError):
            self.converter._get_required_params('unknown')
    
    def test_validate_config(self):
        """Test validating device configuration."""
        # Valid LED
        self.assertTrue(self.converter._validate_config('led', self.led_config))
        
        # Invalid LED (missing pin)
        invalid_led = {
            'type': 'led',
            'initial_state': 'off'
        }
        with self.assertRaises(ValueError):
            self.converter._validate_config('led', invalid_led)
        
        # Valid button
        self.assertTrue(self.converter._validate_config('button', self.button_config))
        
        # Valid traffic light
        self.assertTrue(self.converter._validate_config('traffic_light', self.traffic_light_config))
        
        # Invalid traffic light (missing yellow_pin)
        invalid_traffic_light = {
            'type': 'traffic_light',
            'red_pin': 22,
            'green_pin': 24
        }
        with self.assertRaises(ValueError):
            self.converter._validate_config('traffic_light', invalid_traffic_light)
        
        # Valid display
        self.assertTrue(self.converter._validate_config('display', self.display_config))

if __name__ == '__main__':
    unittest.main()
