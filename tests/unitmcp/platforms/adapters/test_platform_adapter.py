#!/usr/bin/env python3
"""
Unit tests for the platform adapter module.

This module contains tests for the platform adapter implementations.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

from unitmcp.platforms.adapters.platform_adapter import (
    PlatformAdapter,
    RaspberryPiAdapter,
    ArduinoAdapter,
    get_platform_adapter
)


class TestPlatformAdapter(unittest.TestCase):
    """
    Test cases for the PlatformAdapter abstract base class.
    """
    
    def test_abstract_methods(self):
        """
        Test that PlatformAdapter cannot be instantiated directly.
        """
        with self.assertRaises(TypeError):
            PlatformAdapter()


class TestRaspberryPiAdapter(unittest.TestCase):
    """
    Test cases for the RaspberryPiAdapter class.
    """
    
    @patch('unitmcp.platforms.adapters.platform_adapter.GPIO')
    def setUp(self, mock_gpio):
        """
        Set up test fixtures.
        """
        self.mock_gpio = mock_gpio
        self.adapter = RaspberryPiAdapter()
    
    def test_init(self):
        """
        Test initialization of RaspberryPiAdapter.
        """
        self.assertEqual(self.adapter.platform_name, "raspberry_pi")
        self.assertEqual(self.adapter.pin_mode_map, {
            "input": self.mock_gpio.IN,
            "output": self.mock_gpio.OUT,
            "pwm": self.mock_gpio.OUT
        })
        self.assertEqual(self.adapter.pull_mode_map, {
            "up": self.mock_gpio.PUD_UP,
            "down": self.mock_gpio.PUD_DOWN,
            "none": self.mock_gpio.PUD_OFF
        })
        self.assertEqual(self.adapter.active_pwm_pins, {})
    
    def test_initialize(self):
        """
        Test initializing the Raspberry Pi adapter.
        """
        self.adapter.initialize()
        
        self.mock_gpio.setmode.assert_called_once_with(self.mock_gpio.BCM)
        self.mock_gpio.setwarnings.assert_called_once_with(False)
    
    def test_cleanup(self):
        """
        Test cleaning up the Raspberry Pi adapter.
        """
        self.adapter.cleanup()
        
        self.mock_gpio.cleanup.assert_called_once()
    
    def test_setup_pin(self):
        """
        Test setting up a pin on the Raspberry Pi.
        """
        pin = 18
        mode = "output"
        
        self.adapter.setup_pin(pin, mode)
        
        self.mock_gpio.setup.assert_called_once_with(pin, self.mock_gpio.OUT)
    
    def test_setup_pin_with_pull(self):
        """
        Test setting up a pin with a pull resistor on the Raspberry Pi.
        """
        pin = 18
        mode = "input"
        pull = "up"
        
        self.adapter.setup_pin(pin, mode, pull)
        
        self.mock_gpio.setup.assert_called_once_with(pin, self.mock_gpio.IN, pull_up_down=self.mock_gpio.PUD_UP)
    
    def test_setup_pin_invalid_mode(self):
        """
        Test setting up a pin with an invalid mode on the Raspberry Pi.
        """
        pin = 18
        mode = "invalid"
        
        with self.assertRaises(ValueError):
            self.adapter.setup_pin(pin, mode)
    
    def test_setup_pin_invalid_pull(self):
        """
        Test setting up a pin with an invalid pull resistor on the Raspberry Pi.
        """
        pin = 18
        mode = "input"
        pull = "invalid"
        
        with self.assertRaises(ValueError):
            self.adapter.setup_pin(pin, mode, pull)
    
    def test_set_pin_value(self):
        """
        Test setting a pin value on the Raspberry Pi.
        """
        pin = 18
        value = 1
        
        self.adapter.set_pin_value(pin, value)
        
        self.mock_gpio.output.assert_called_once_with(pin, value)
    
    def test_get_pin_value(self):
        """
        Test getting a pin value from the Raspberry Pi.
        """
        pin = 18
        expected_value = 1
        
        self.mock_gpio.input.return_value = expected_value
        
        value = self.adapter.get_pin_value(pin)
        
        self.mock_gpio.input.assert_called_once_with(pin)
        self.assertEqual(value, expected_value)
    
    def test_setup_pwm(self):
        """
        Test setting up PWM on the Raspberry Pi.
        """
        pin = 18
        frequency = 100
        
        # Mock the PWM class
        mock_pwm = MagicMock()
        self.mock_gpio.PWM.return_value = mock_pwm
        
        self.adapter.setup_pwm(pin, frequency)
        
        self.mock_gpio.setup.assert_called_once_with(pin, self.mock_gpio.OUT)
        self.mock_gpio.PWM.assert_called_once_with(pin, frequency)
        mock_pwm.start.assert_called_once_with(0)
        self.assertEqual(self.adapter.active_pwm_pins[pin], mock_pwm)
    
    def test_set_pwm_duty_cycle(self):
        """
        Test setting the PWM duty cycle on the Raspberry Pi.
        """
        pin = 18
        duty_cycle = 50
        
        # Mock the PWM instance
        mock_pwm = MagicMock()
        self.adapter.active_pwm_pins[pin] = mock_pwm
        
        self.adapter.set_pwm_duty_cycle(pin, duty_cycle)
        
        mock_pwm.ChangeDutyCycle.assert_called_once_with(duty_cycle)
    
    def test_set_pwm_duty_cycle_pin_not_setup(self):
        """
        Test setting the PWM duty cycle on a pin that hasn't been set up.
        """
        pin = 18
        duty_cycle = 50
        
        with self.assertRaises(ValueError):
            self.adapter.set_pwm_duty_cycle(pin, duty_cycle)
    
    def test_cleanup_pwm(self):
        """
        Test cleaning up PWM on the Raspberry Pi.
        """
        pin = 18
        
        # Mock the PWM instance
        mock_pwm = MagicMock()
        self.adapter.active_pwm_pins[pin] = mock_pwm
        
        self.adapter.cleanup_pwm(pin)
        
        mock_pwm.stop.assert_called_once()
        self.assertNotIn(pin, self.adapter.active_pwm_pins)
    
    def test_cleanup_pwm_pin_not_setup(self):
        """
        Test cleaning up PWM on a pin that hasn't been set up.
        """
        pin = 18
        
        # This should not raise an exception
        self.adapter.cleanup_pwm(pin)


class TestArduinoAdapter(unittest.TestCase):
    """
    Test cases for the ArduinoAdapter class.
    """
    
    @patch('unitmcp.platforms.adapters.platform_adapter.serial.Serial')
    def setUp(self, mock_serial):
        """
        Set up test fixtures.
        """
        self.mock_serial = mock_serial
        self.adapter = ArduinoAdapter(port="/dev/ttyUSB0", baud_rate=9600)
    
    def test_init(self):
        """
        Test initialization of ArduinoAdapter.
        """
        self.assertEqual(self.adapter.platform_name, "arduino")
        self.assertEqual(self.adapter.port, "/dev/ttyUSB0")
        self.assertEqual(self.adapter.baud_rate, 9600)
        self.assertEqual(self.adapter.timeout, 1.0)
        self.assertIsNone(self.adapter.serial_connection)
    
    def test_initialize(self):
        """
        Test initializing the Arduino adapter.
        """
        # Mock the serial connection
        mock_connection = MagicMock()
        self.mock_serial.return_value = mock_connection
        
        self.adapter.initialize()
        
        self.mock_serial.assert_called_once_with(
            port="/dev/ttyUSB0",
            baudrate=9600,
            timeout=1.0
        )
        self.assertEqual(self.adapter.serial_connection, mock_connection)
    
    def test_cleanup(self):
        """
        Test cleaning up the Arduino adapter.
        """
        # Mock the serial connection
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        
        self.adapter.cleanup()
        
        mock_connection.close.assert_called_once()
        self.assertIsNone(self.adapter.serial_connection)
    
    def test_cleanup_no_connection(self):
        """
        Test cleaning up the Arduino adapter with no connection.
        """
        # This should not raise an exception
        self.adapter.cleanup()
    
    def test_send_command(self):
        """
        Test sending a command to the Arduino.
        """
        # Mock the serial connection
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        
        command = "PIN:18:OUTPUT"
        
        self.adapter.send_command(command)
        
        mock_connection.write.assert_called_once_with(f"{command}\n".encode())
    
    def test_send_command_no_connection(self):
        """
        Test sending a command to the Arduino with no connection.
        """
        command = "PIN:18:OUTPUT"
        
        with self.assertRaises(ValueError):
            self.adapter.send_command(command)
    
    def test_read_response(self):
        """
        Test reading a response from the Arduino.
        """
        # Mock the serial connection
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        
        expected_response = "OK"
        mock_connection.readline.return_value = f"{expected_response}\n".encode()
        
        response = self.adapter.read_response()
        
        mock_connection.readline.assert_called_once()
        self.assertEqual(response, expected_response)
    
    def test_read_response_no_connection(self):
        """
        Test reading a response from the Arduino with no connection.
        """
        with self.assertRaises(ValueError):
            self.adapter.read_response()
    
    def test_setup_pin(self):
        """
        Test setting up a pin on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        mode = "output"
        
        self.adapter.setup_pin(pin, mode)
        
        mock_connection.write.assert_called_once_with(f"PIN:{pin}:{mode.upper()}\n".encode())
    
    def test_setup_pin_with_pull(self):
        """
        Test setting up a pin with a pull resistor on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        mode = "input"
        pull = "up"
        
        self.adapter.setup_pin(pin, mode, pull)
        
        mock_connection.write.assert_called_once_with(f"PIN:{pin}:{mode.upper()}:{pull.upper()}\n".encode())
    
    def test_set_pin_value(self):
        """
        Test setting a pin value on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        value = 1
        
        self.adapter.set_pin_value(pin, value)
        
        mock_connection.write.assert_called_once_with(f"WRITE:{pin}:{value}\n".encode())
    
    def test_get_pin_value(self):
        """
        Test getting a pin value from the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "1\n".encode()
        
        pin = 18
        expected_value = 1
        
        value = self.adapter.get_pin_value(pin)
        
        mock_connection.write.assert_called_once_with(f"READ:{pin}\n".encode())
        self.assertEqual(value, expected_value)
    
    def test_setup_pwm(self):
        """
        Test setting up PWM on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        frequency = 100
        
        self.adapter.setup_pwm(pin, frequency)
        
        mock_connection.write.assert_called_once_with(f"PWM:{pin}:{frequency}\n".encode())
    
    def test_set_pwm_duty_cycle(self):
        """
        Test setting the PWM duty cycle on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        duty_cycle = 50
        
        self.adapter.set_pwm_duty_cycle(pin, duty_cycle)
        
        mock_connection.write.assert_called_once_with(f"PWM:{pin}:{duty_cycle}\n".encode())
    
    def test_cleanup_pwm(self):
        """
        Test cleaning up PWM on the Arduino.
        """
        # Mock the serial connection and response
        mock_connection = MagicMock()
        self.adapter.serial_connection = mock_connection
        mock_connection.readline.return_value = "OK\n".encode()
        
        pin = 18
        
        self.adapter.cleanup_pwm(pin)
        
        mock_connection.write.assert_called_once_with(f"PWM:{pin}:0\n".encode())


class TestGetPlatformAdapter(unittest.TestCase):
    """
    Test cases for the get_platform_adapter function.
    """
    
    @patch('unitmcp.platforms.adapters.platform_adapter.RaspberryPiAdapter')
    def test_get_raspberry_pi_adapter(self, mock_rpi_adapter):
        """
        Test getting a Raspberry Pi adapter.
        """
        # Mock the adapter
        mock_adapter = MagicMock()
        mock_rpi_adapter.return_value = mock_adapter
        
        adapter = get_platform_adapter("raspberry_pi")
        
        self.assertEqual(adapter, mock_adapter)
        mock_rpi_adapter.assert_called_once()
    
    @patch('unitmcp.platforms.adapters.platform_adapter.ArduinoAdapter')
    def test_get_arduino_adapter(self, mock_arduino_adapter):
        """
        Test getting an Arduino adapter.
        """
        # Mock the adapter
        mock_adapter = MagicMock()
        mock_arduino_adapter.return_value = mock_adapter
        
        adapter = get_platform_adapter("arduino", port="/dev/ttyUSB0", baud_rate=9600)
        
        self.assertEqual(adapter, mock_adapter)
        mock_arduino_adapter.assert_called_once_with(port="/dev/ttyUSB0", baud_rate=9600)
    
    def test_get_unknown_adapter(self):
        """
        Test getting an unknown adapter type.
        """
        with self.assertRaises(ValueError):
            get_platform_adapter("unknown")


if __name__ == '__main__':
    unittest.main()
