#!/usr/bin/env python3
"""
Unit tests for the device factory module.

This module contains tests for the device factory implementations.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.hardware.device_factory import (
    Device,
    LEDDevice,
    ButtonDevice,
    DeviceFactory,
    GPIODeviceFactory,
    get_device_factory,
    register_device_factory,
    create_device
)


class TestDevice(unittest.TestCase):
    """
    Test cases for the Device abstract base class.
    """
    
    def test_abstract_methods(self):
        """
        Test that Device cannot be instantiated directly.
        """
        with self.assertRaises(TypeError):
            Device("test_device")


class TestLEDDevice(unittest.TestCase):
    """
    Test cases for the LEDDevice class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.device = LEDDevice("test_led", 18)
    
    def test_init(self):
        """
        Test initialization of LEDDevice.
        """
        self.assertEqual(self.device.device_id, "test_led")
        self.assertEqual(self.device.pin, 18)
        self.assertFalse(self.device.state)
        self.assertIsNone(self.device.blink_task)
        self.assertFalse(self.device.is_initialized)
    
    async def async_test_initialize(self):
        """
        Test initializing the LED device.
        """
        result = await self.device.initialize()
        self.assertTrue(result)
        self.assertTrue(self.device.is_initialized)
    
    async def async_test_cleanup(self):
        """
        Test cleaning up the LED device.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Then clean it up
        result = await self.device.cleanup()
        self.assertTrue(result)
        self.assertFalse(self.device.is_initialized)
    
    async def async_test_execute_command_not_initialized(self):
        """
        Test executing a command on an uninitialized device.
        """
        result = await self.device.execute_command("on", {})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Device not initialized")
    
    async def async_test_execute_command_on(self):
        """
        Test executing the 'on' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("on", {})
        self.assertTrue(result["success"])
        self.assertTrue(result["state"])
        self.assertTrue(self.device.state)
    
    async def async_test_execute_command_off(self):
        """
        Test executing the 'off' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Turn on the device
        await self.device.execute_command("on", {})
        
        # Execute the command
        result = await self.device.execute_command("off", {})
        self.assertTrue(result["success"])
        self.assertFalse(result["state"])
        self.assertFalse(self.device.state)
    
    async def async_test_execute_command_toggle(self):
        """
        Test executing the 'toggle' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Toggle from off to on
        result = await self.device.execute_command("toggle", {})
        self.assertTrue(result["success"])
        self.assertTrue(result["state"])
        self.assertTrue(self.device.state)
        
        # Toggle from on to off
        result = await self.device.execute_command("toggle", {})
        self.assertTrue(result["success"])
        self.assertFalse(result["state"])
        self.assertFalse(self.device.state)
    
    async def async_test_execute_command_blink(self):
        """
        Test executing the 'blink' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("blink", {
            "on_time": 0.1,
            "off_time": 0.1,
            "count": 2
        })
        self.assertTrue(result["success"])
        self.assertEqual(result["on_time"], 0.1)
        self.assertEqual(result["off_time"], 0.1)
        self.assertEqual(result["count"], 2)
        self.assertIsNotNone(self.device.blink_task)
        
        # Wait for the blink task to complete
        await asyncio.sleep(0.5)
        
        # Check that the blink task is done
        self.assertTrue(self.device.blink_task.done())
    
    async def async_test_execute_command_unknown(self):
        """
        Test executing an unknown command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("unknown", {})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unknown command: unknown")
    
    def test_initialize(self):
        """
        Test the initialize method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_initialize())
        finally:
            loop.close()
    
    def test_cleanup(self):
        """
        Test the cleanup method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_cleanup())
        finally:
            loop.close()
    
    def test_execute_command_not_initialized(self):
        """
        Test executing a command on an uninitialized device.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_not_initialized())
        finally:
            loop.close()
    
    def test_execute_command_on(self):
        """
        Test executing the 'on' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_on())
        finally:
            loop.close()
    
    def test_execute_command_off(self):
        """
        Test executing the 'off' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_off())
        finally:
            loop.close()
    
    def test_execute_command_toggle(self):
        """
        Test executing the 'toggle' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_toggle())
        finally:
            loop.close()
    
    def test_execute_command_blink(self):
        """
        Test executing the 'blink' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_blink())
        finally:
            loop.close()
    
    def test_execute_command_unknown(self):
        """
        Test executing an unknown command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_unknown())
        finally:
            loop.close()


class TestButtonDevice(unittest.TestCase):
    """
    Test cases for the ButtonDevice class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.device = ButtonDevice("test_button", 17)
    
    def test_init(self):
        """
        Test initialization of ButtonDevice.
        """
        self.assertEqual(self.device.device_id, "test_button")
        self.assertEqual(self.device.pin, 17)
        self.assertFalse(self.device.is_pressed)
        self.assertEqual(self.device.press_callbacks, [])
        self.assertFalse(self.device.is_initialized)
    
    async def async_test_initialize(self):
        """
        Test initializing the button device.
        """
        result = await self.device.initialize()
        self.assertTrue(result)
        self.assertTrue(self.device.is_initialized)
    
    async def async_test_cleanup(self):
        """
        Test cleaning up the button device.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Then clean it up
        result = await self.device.cleanup()
        self.assertTrue(result)
        self.assertFalse(self.device.is_initialized)
    
    async def async_test_execute_command_not_initialized(self):
        """
        Test executing a command on an uninitialized device.
        """
        result = await self.device.execute_command("read", {})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Device not initialized")
    
    async def async_test_execute_command_read(self):
        """
        Test executing the 'read' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("read", {})
        self.assertTrue(result["success"])
        self.assertFalse(result["is_pressed"])
    
    async def async_test_execute_command_register_callback(self):
        """
        Test executing the 'register_callback' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Create a callback function
        callback = MagicMock()
        
        # Execute the command
        result = await self.device.execute_command("register_callback", {
            "callback": callback
        })
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Callback registered")
        self.assertEqual(len(self.device.press_callbacks), 1)
        self.assertEqual(self.device.press_callbacks[0], callback)
    
    async def async_test_execute_command_register_callback_invalid(self):
        """
        Test executing the 'register_callback' command with an invalid callback.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("register_callback", {
            "callback": "not_a_function"
        })
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid callback")
        self.assertEqual(len(self.device.press_callbacks), 0)
    
    async def async_test_execute_command_simulate_press(self):
        """
        Test executing the 'simulate_press' command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Create a callback function
        callback = MagicMock()
        
        # Register the callback
        await self.device.execute_command("register_callback", {
            "callback": callback
        })
        
        # Execute the command
        result = await self.device.execute_command("simulate_press", {})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Press simulated")
        self.assertTrue(self.device.is_pressed)
        
        # Check that the callback was called
        callback.assert_called_once_with("test_button", True)
        
        # Wait for the button to reset
        await asyncio.sleep(0.2)
        
        # Check that the button was reset
        self.assertFalse(self.device.is_pressed)
        
        # Check that the callback was called again
        self.assertEqual(callback.call_count, 2)
        callback.assert_called_with("test_button", False)
    
    async def async_test_execute_command_unknown(self):
        """
        Test executing an unknown command.
        """
        # First initialize the device
        await self.device.initialize()
        
        # Execute the command
        result = await self.device.execute_command("unknown", {})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Unknown command: unknown")
    
    def test_initialize(self):
        """
        Test the initialize method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_initialize())
        finally:
            loop.close()
    
    def test_cleanup(self):
        """
        Test the cleanup method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_cleanup())
        finally:
            loop.close()
    
    def test_execute_command_not_initialized(self):
        """
        Test executing a command on an uninitialized device.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_not_initialized())
        finally:
            loop.close()
    
    def test_execute_command_read(self):
        """
        Test executing the 'read' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_read())
        finally:
            loop.close()
    
    def test_execute_command_register_callback(self):
        """
        Test executing the 'register_callback' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_register_callback())
        finally:
            loop.close()
    
    def test_execute_command_register_callback_invalid(self):
        """
        Test executing the 'register_callback' command with an invalid callback.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_register_callback_invalid())
        finally:
            loop.close()
    
    def test_execute_command_simulate_press(self):
        """
        Test executing the 'simulate_press' command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_simulate_press())
        finally:
            loop.close()
    
    def test_execute_command_unknown(self):
        """
        Test executing an unknown command.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_execute_command_unknown())
        finally:
            loop.close()


class TestDeviceFactory(unittest.TestCase):
    """
    Test cases for the DeviceFactory abstract base class.
    """
    
    def test_abstract_methods(self):
        """
        Test that DeviceFactory cannot be instantiated directly.
        """
        with self.assertRaises(TypeError):
            DeviceFactory()


class TestGPIODeviceFactory(unittest.TestCase):
    """
    Test cases for the GPIODeviceFactory class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.factory = GPIODeviceFactory()
    
    def test_create_device_led(self):
        """
        Test creating an LED device.
        """
        device = self.factory.create_device("test_led", "led", pin=18)
        self.assertIsInstance(device, LEDDevice)
        self.assertEqual(device.device_id, "test_led")
        self.assertEqual(device.pin, 18)
    
    def test_create_device_button(self):
        """
        Test creating a button device.
        """
        device = self.factory.create_device("test_button", "button", pin=17)
        self.assertIsInstance(device, ButtonDevice)
        self.assertEqual(device.device_id, "test_button")
        self.assertEqual(device.pin, 17)
    
    def test_create_device_led_missing_pin(self):
        """
        Test creating an LED device with a missing pin parameter.
        """
        device = self.factory.create_device("test_led", "led")
        self.assertIsNone(device)
    
    def test_create_device_button_missing_pin(self):
        """
        Test creating a button device with a missing pin parameter.
        """
        device = self.factory.create_device("test_button", "button")
        self.assertIsNone(device)
    
    def test_create_device_unknown(self):
        """
        Test creating an unknown device type.
        """
        device = self.factory.create_device("test_device", "unknown")
        self.assertIsNone(device)


class TestFactoryRegistry(unittest.TestCase):
    """
    Test cases for the factory registry functions.
    """
    
    def test_get_device_factory(self):
        """
        Test getting a device factory from the registry.
        """
        factory = get_device_factory("gpio")
        self.assertIsInstance(factory, GPIODeviceFactory)
    
    def test_get_device_factory_unknown(self):
        """
        Test getting an unknown device factory from the registry.
        """
        factory = get_device_factory("unknown")
        self.assertIsNone(factory)
    
    def test_register_device_factory(self):
        """
        Test registering a device factory in the registry.
        """
        # Create a mock factory
        mock_factory = MagicMock(spec=DeviceFactory)
        
        # Register the factory
        register_device_factory("mock", mock_factory)
        
        # Get the factory
        factory = get_device_factory("mock")
        self.assertEqual(factory, mock_factory)
    
    def test_create_device(self):
        """
        Test creating a device using the create_device function.
        """
        device = create_device("gpio", "test_led", "led", pin=18)
        self.assertIsInstance(device, LEDDevice)
        self.assertEqual(device.device_id, "test_led")
        self.assertEqual(device.pin, 18)
    
    def test_create_device_unknown_factory(self):
        """
        Test creating a device with an unknown factory type.
        """
        with self.assertRaises(ValueError):
            create_device("unknown", "test_device", "led", pin=18)


if __name__ == '__main__':
    unittest.main()
