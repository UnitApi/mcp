#!/usr/bin/env python3
"""
Unit tests for the UnitMCP DSL Compiler.

These tests verify that the DSL compiler correctly parses and compiles
different DSL formats into UnitMCP commands and configurations.
"""

import os
import sys
import unittest
import yaml
import json
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.compiler import DslCompiler

class TestDslCompiler(unittest.TestCase):
    """Test cases for the DSL compiler."""
    
    def setUp(self):
        """Set up the test environment."""
        self.compiler = DslCompiler()
        
        # Test data
        self.yaml_content = """
        devices:
          test_led:
            type: led
            pin: 17
        """
        
        self.json_content = """
        {
          "devices": {
            "test_led": {
              "type": "led",
              "pin": 17
            }
          }
        }
        """
        
        self.text_content = "test_button -> test_led"
    
    def test_detect_format_yaml(self):
        """Test format detection for YAML content."""
        format_type = self.compiler._detect_format(self.yaml_content)
        self.assertEqual(format_type, 'yaml')
    
    def test_detect_format_json(self):
        """Test format detection for JSON content."""
        format_type = self.compiler._detect_format(self.json_content)
        self.assertEqual(format_type, 'json')
    
    def test_detect_format_text(self):
        """Test format detection for text content."""
        format_type = self.compiler._detect_format(self.text_content)
        self.assertEqual(format_type, 'text')
    
    def test_parse_yaml(self):
        """Test parsing YAML content."""
        result = self.compiler._parse_yaml(self.yaml_content)
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertIn('test_led', result['devices'])
        self.assertEqual(result['devices']['test_led']['pin'], 17)
    
    def test_parse_json(self):
        """Test parsing JSON content."""
        result = self.compiler._parse_json(self.json_content)
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertIn('test_led', result['devices'])
        self.assertEqual(result['devices']['test_led']['pin'], 17)
    
    def test_parse_text(self):
        """Test parsing text content."""
        result = self.compiler._parse_text(self.text_content)
        self.assertIsInstance(result, dict)
        self.assertIn('trigger', result)
        self.assertIn('action', result)
        self.assertEqual(result['trigger'], 'test_button')
        self.assertEqual(result['action'], 'test_led')
    
    def test_compile_yaml(self):
        """Test compiling YAML content."""
        result = self.compiler.compile(self.yaml_content, 'yaml')
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
    
    def test_compile_json(self):
        """Test compiling JSON content."""
        result = self.compiler.compile(self.json_content, 'json')
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
    
    def test_compile_text(self):
        """Test compiling text content."""
        result = self.compiler.compile(self.text_content, 'text')
        self.assertIsInstance(result, dict)
        self.assertTrue('trigger' in result or 'command' in result)
    
    def test_compile_auto_detect(self):
        """Test compiling with auto-detection of format."""
        # YAML
        result = self.compiler.compile(self.yaml_content)
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        
        # JSON
        result = self.compiler.compile(self.json_content)
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        
        # Text
        result = self.compiler.compile(self.text_content)
        self.assertIsInstance(result, dict)
        self.assertTrue('trigger' in result or 'command' in result)
    
    def test_invalid_yaml(self):
        """Test handling invalid YAML content."""
        invalid_yaml = """
        devices:
          test_led:
            type: led
            pin: 17
          invalid:
            - item1
          - item2
        """
        with self.assertRaises(ValueError):
            self.compiler.compile(invalid_yaml, 'yaml')
    
    def test_invalid_json(self):
        """Test handling invalid JSON content."""
        invalid_json = """
        {
          "devices": {
            "test_led": {
              "type": "led",
              "pin": 17
            }
          },
        }
        """
        with self.assertRaises(ValueError):
            self.compiler.compile(invalid_json, 'json')
    
    def test_empty_content(self):
        """Test handling empty content."""
        with self.assertRaises(ValueError):
            self.compiler.compile("")
    
    def test_unsupported_format(self):
        """Test handling unsupported format."""
        with self.assertRaises(ValueError):
            self.compiler.compile(self.yaml_content, 'unsupported')
    
    def test_convert_device_config(self):
        """Test converting device configuration."""
        config = {
            'devices': {
                'test_led': {
                    'type': 'led',
                    'pin': 17
                }
            }
        }
        result = self.compiler._convert_device_config(config)
        self.assertEqual(result, config)
    
    def test_convert_automation(self):
        """Test converting automation configuration."""
        config = {
            'automation': {
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
        result = self.compiler._convert_automation(config)
        self.assertEqual(result, config)
    
    def test_convert_flow(self):
        """Test converting flow configuration."""
        config = {
            'nodes': [
                {
                    'id': 'test_button',
                    'type': 'button',
                    'pin': 17
                },
                {
                    'id': 'test_led',
                    'type': 'led',
                    'pin': 18
                }
            ],
            'wires': [
                {
                    'source': 'test_button',
                    'target': 'test_led'
                }
            ]
        }
        result = self.compiler._convert_flow(config)
        self.assertEqual(result, config)
    
    def test_convert_command(self):
        """Test converting command."""
        config = {
            'command': 'activate',
            'device': 'test_led'
        }
        result = self.compiler._convert_command(config)
        self.assertEqual(result, config)

if __name__ == '__main__':
    unittest.main()
