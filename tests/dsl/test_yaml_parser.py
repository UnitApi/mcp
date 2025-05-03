#!/usr/bin/env python3
"""
Unit tests for the UnitMCP YAML Config Parser.

These tests verify that the YAML parser correctly parses and validates
YAML-based device and automation configurations.
"""

import os
import sys
import unittest
import yaml
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.formats.yaml_parser import YamlConfigParser

class TestYamlConfigParser(unittest.TestCase):
    """Test cases for the YAML config parser."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = YamlConfigParser()
        
        # Test data
        self.valid_config = """
        unitmcp:
          name: "test-controller"
          platform: simulation
          mode: simulation

        devices:
          test_led:
            type: led
            pin: 17
            initial_state: off
          
          test_button:
            type: button
            pin: 27
            pull_up: true
        
        automations:
          test_automation:
            trigger:
              platform: state
              entity_id: test_button
              to: "on"
            action:
              service: activate
              entity_id: test_led
        """
        
        self.invalid_config = """
        unitmcp:
          name: "test-controller"
          platform: simulation
          mode: simulation

        devices:
          test_led:
            type: led
            # Missing required pin
            initial_state: off
        """
        
        self.list_format_config = """
        unitmcp:
          name: "test-controller"
          platform: simulation
          mode: simulation

        devices:
          - name: test_led
            type: led
            pin: 17
            initial_state: off
          
          - name: test_button
            type: button
            pin: 27
            pull_up: true
        """
    
    def test_parse_valid_config(self):
        """Test parsing a valid YAML configuration."""
        result = self.parser.parse(self.valid_config)
        self.assertIsInstance(result, dict)
        self.assertIn('unitmcp', result)
        self.assertIn('devices', result)
        self.assertIn('automations', result)
        self.assertIn('test_led', result['devices'])
        self.assertIn('test_button', result['devices'])
        self.assertIn('test_automation', result['automations'])
    
    def test_parse_invalid_config(self):
        """Test parsing an invalid YAML configuration."""
        with self.assertRaises(ValueError):
            self.parser.parse(self.invalid_config)
    
    def test_parse_list_format(self):
        """Test parsing a YAML configuration with list format for devices."""
        result = self.parser.parse(self.list_format_config)
        self.assertIsInstance(result, dict)
        self.assertIn('unitmcp', result)
        self.assertIn('devices', result)
        self.assertIn('test_led', result['devices'])
        self.assertIn('test_button', result['devices'])
    
    def test_validate_device_config(self):
        """Test validating device configuration."""
        # Valid device
        valid_device = {
            'type': 'led',
            'pin': 17
        }
        self.assertTrue(self.parser._validate_device_config('test_led', valid_device))
        
        # Invalid device (missing pin)
        invalid_device = {
            'type': 'led'
        }
        with self.assertRaises(ValueError):
            self.parser._validate_device_config('test_led', invalid_device)
        
        # Invalid device (unknown type)
        unknown_type = {
            'type': 'unknown',
            'pin': 17
        }
        with self.assertRaises(ValueError):
            self.parser._validate_device_config('test_led', unknown_type)
    
    def test_validate_automation_config(self):
        """Test validating automation configuration."""
        # Valid automation
        valid_automation = {
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
        self.assertTrue(self.parser._validate_automation_config('test_automation', valid_automation))
        
        # Invalid automation (missing trigger)
        invalid_automation = {
            'action': {
                'service': 'activate',
                'entity_id': 'test_led'
            }
        }
        with self.assertRaises(ValueError):
            self.parser._validate_automation_config('test_automation', invalid_automation)
        
        # Invalid automation (missing action)
        invalid_automation = {
            'trigger': {
                'platform': 'state',
                'entity_id': 'test_button',
                'to': 'on'
            }
        }
        with self.assertRaises(ValueError):
            self.parser._validate_automation_config('test_automation', invalid_automation)
    
    def test_normalize_list_format(self):
        """Test normalizing list format to dictionary format."""
        list_format = [
            {
                'name': 'test_led',
                'type': 'led',
                'pin': 17
            },
            {
                'name': 'test_button',
                'type': 'button',
                'pin': 27
            }
        ]
        
        expected = {
            'test_led': {
                'type': 'led',
                'pin': 17
            },
            'test_button': {
                'type': 'button',
                'pin': 27
            }
        }
        
        result = self.parser._normalize_list_format(list_format)
        self.assertEqual(result, expected)
    
    def test_normalize_list_format_missing_name(self):
        """Test normalizing list format with missing name."""
        list_format = [
            {
                'type': 'led',
                'pin': 17
            }
        ]
        
        with self.assertRaises(ValueError):
            self.parser._normalize_list_format(list_format)
    
    def test_normalize_list_format_duplicate_name(self):
        """Test normalizing list format with duplicate name."""
        list_format = [
            {
                'name': 'test_led',
                'type': 'led',
                'pin': 17
            },
            {
                'name': 'test_led',
                'type': 'button',
                'pin': 27
            }
        ]
        
        with self.assertRaises(ValueError):
            self.parser._normalize_list_format(list_format)

if __name__ == '__main__':
    unittest.main()
