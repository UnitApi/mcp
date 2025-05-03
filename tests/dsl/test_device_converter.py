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
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.converters.to_devices import DeviceConverter

class MockDeviceFactory:
    """Mock implementation of DeviceFactory for testing."""
    
    async def create_device(self, device_type, **config):
        """Create a mock device."""
        # Sprawdź, czy typ urządzenia jest obsługiwany
        if device_type not in ['led', 'button', 'display', 'traffic_light']:
            raise ValueError(f"Unknown device type: {device_type}")
            
        # Wywołaj odpowiednią metodę tworzenia urządzenia
        create_method = getattr(self, f"create_{device_type}")
        return await create_method(device_id="test_device", **config)
    
    async def create_led(self, device_id, **config):
        """Create a mock LED device."""
        # Sprawdź wymagane parametry
        if 'pin' not in config:
            raise ValueError(f"LED device '{device_id}' requires 'pin' parameter")
            
        mock_led = MagicMock()
        mock_led.device_type = 'led'
        mock_led.device_id = device_id
        mock_led.config = config
        return mock_led
    
    async def create_button(self, device_id, **config):
        """Create a mock button device."""
        # Sprawdź wymagane parametry
        if 'pin' not in config:
            raise ValueError(f"Button device '{device_id}' requires 'pin' parameter")
            
        mock_button = MagicMock()
        mock_button.device_type = 'button'
        mock_button.device_id = device_id
        mock_button.config = config
        return mock_button
    
    async def create_display(self, device_id, **config):
        """Create a mock display device."""
        # Sprawdź wymagane parametry
        if 'display_type' not in config:
            raise ValueError(f"Display device '{device_id}' requires 'display_type' parameter")
            
        mock_display = MagicMock()
        mock_display.device_type = 'display'
        mock_display.device_id = device_id
        mock_display.config = config
        return mock_display
    
    async def create_traffic_light(self, device_id, **config):
        """Create a mock traffic light device."""
        # Sprawdź wymagane parametry
        required_params = ['red_pin', 'yellow_pin', 'green_pin']
        for param in required_params:
            if param not in config:
                raise ValueError(f"Traffic light device '{device_id}' requires '{param}' parameter")
                
        mock_traffic_light = MagicMock()
        mock_traffic_light.device_type = 'traffic_light'
        mock_traffic_light.device_id = device_id
        mock_traffic_light.config = config
        return mock_traffic_light

class TestDeviceConverter(unittest.IsolatedAsyncioTestCase):
    """Test cases for the device converter."""
    
    def setUp(self):
        """Set up the test environment."""
        self.mock_factory = MockDeviceFactory()
        self.converter = DeviceConverter(device_factory=self.mock_factory)
        
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
    
    async def test_convert_led(self):
        """Test converting LED device configuration."""
        # Przygotuj konfigurację z urządzeniem LED
        config = {
            'devices': {
                'test_led': self.led_config
            }
        }
        
        # Konwertuj urządzenia
        devices = await self.converter.convert_to_devices(config)
        
        # Sprawdź, czy urządzenie zostało utworzone poprawnie
        self.assertIn('test_led', devices)
        device = devices['test_led']
        self.assertEqual(device.device_type, 'led')
        self.assertEqual(device.device_id, 'test_led')
    
    async def test_convert_button(self):
        """Test converting button device configuration."""
        # Przygotuj konfigurację z przyciskiem
        config = {
            'devices': {
                'test_button': self.button_config
            }
        }
        
        # Konwertuj urządzenia
        devices = await self.converter.convert_to_devices(config)
        
        # Sprawdź, czy urządzenie zostało utworzone poprawnie
        self.assertIn('test_button', devices)
        device = devices['test_button']
        self.assertEqual(device.device_type, 'button')
        self.assertEqual(device.device_id, 'test_button')
    
    async def test_convert_traffic_light(self):
        """Test converting traffic light device configuration."""
        # Przygotuj konfigurację z sygnalizatorem
        config = {
            'devices': {
                'test_traffic_light': self.traffic_light_config
            }
        }
        
        # Konwertuj urządzenia
        devices = await self.converter.convert_to_devices(config)
        
        # Sprawdź, czy urządzenie zostało utworzone poprawnie
        self.assertIn('test_traffic_light', devices)
        device = devices['test_traffic_light']
        self.assertEqual(device.device_type, 'traffic_light')
        self.assertEqual(device.device_id, 'test_traffic_light')
    
    async def test_convert_display(self):
        """Test converting display device configuration."""
        # Przygotuj konfigurację z wyświetlaczem
        config = {
            'devices': {
                'test_display': self.display_config
            }
        }
        
        # Konwertuj urządzenia
        devices = await self.converter.convert_to_devices(config)
        
        # Sprawdź, czy urządzenie zostało utworzone poprawnie
        self.assertIn('test_display', devices)
        device = devices['test_display']
        self.assertEqual(device.device_type, 'display')
        self.assertEqual(device.device_id, 'test_display')
    
    async def test_convert_unknown_type(self):
        """Test converting unknown device type."""
        # Przygotuj konfigurację z nieznanym typem urządzenia
        config = {
            'devices': {
                'test_unknown': {
                    'type': 'unknown',
                    'pin': 17
                }
            }
        }
        
        # Sprawdź, czy zostanie zgłoszony wyjątek
        with self.assertRaises(ValueError):
            await self.converter.convert_to_devices(config)
    
    async def test_convert_missing_required_param(self):
        """Test converting device with missing required parameter."""
        # Przygotuj konfigurację z brakującym parametrem
        config = {
            'devices': {
                'test_led': {
                    'type': 'led'
                    # Brak wymaganego parametru pin
                }
            }
        }
        
        # Sprawdź, czy zostanie zgłoszony wyjątek
        with self.assertRaises(ValueError):
            await self.converter.convert_to_devices(config)
    
    async def test_missing_devices_section(self):
        """Test converting configuration without devices section."""
        # Przygotuj konfigurację bez sekcji devices
        config = {}
        
        # Sprawdź, czy zostanie zgłoszony wyjątek
        with self.assertRaises(ValueError):
            await self.converter.convert_to_devices(config)
    
    async def test_list_format_devices(self):
        """Test converting devices in list format."""
        # Przygotuj konfigurację z urządzeniami w formacie listy
        config = {
            'devices': [
                {
                    'name': 'test_led',
                    'type': 'led',
                    'pin': 17,
                    'initial_state': 'off'
                }
            ]
        }
        
        # Konwertuj urządzenia
        devices = await self.converter.convert_to_devices(config)
        
        # Sprawdź, czy urządzenie zostało utworzone poprawnie
        self.assertIn('test_led', devices)
        device = devices['test_led']
        self.assertEqual(device.device_type, 'led')
        self.assertEqual(device.device_id, 'test_led')

if __name__ == '__main__':
    unittest.main()
