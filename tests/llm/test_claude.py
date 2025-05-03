#!/usr/bin/env python3
"""
Unit tests for the UnitMCP Claude 3.7 Integration.

These tests verify that the Claude 3.7 integration correctly processes
natural language commands and converts them to UnitMCP commands.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.llm.claude import ClaudeIntegration

class TestClaudeIntegration(unittest.TestCase):
    """Test cases for the Claude 3.7 integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create the integration
        self.integration = ClaudeIntegration()
        
        # Test data
        self.test_commands = [
            "Turn on the kitchen light",
            "Turn off the living room light",
            "Set the thermostat to 72 degrees",
            "What is the system status?",
            "Enable the morning automation"
        ]
    
    def test_init_no_api_key(self):
        """Test initialization without API key."""
        integration = ClaudeIntegration()
        self.assertIsNone(integration.api_key)
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        integration = ClaudeIntegration(api_key="test_api_key")
        self.assertEqual(integration.api_key, "test_api_key")
    
    def test_load_prompts(self):
        """Test loading prompts."""
        self.integration._load_prompts()
        self.assertIsInstance(self.integration._prompts, dict)
        self.assertIn('device_control', self.integration._prompts)
        self.assertIn('automation', self.integration._prompts)
        self.assertIn('system', self.integration._prompts)
        self.assertIn('general', self.integration._prompts)
    
    def test_load_prompt(self):
        """Test loading a prompt template."""
        # Device control prompt
        prompt = self.integration._load_prompt('device_control')
        self.assertIsInstance(prompt, str)
        self.assertIn('{command}', prompt)
        
        # Automation prompt
        prompt = self.integration._load_prompt('automation')
        self.assertIsInstance(prompt, str)
        self.assertIn('{command}', prompt)
        
        # System prompt
        prompt = self.integration._load_prompt('system')
        self.assertIsInstance(prompt, str)
        self.assertIn('{command}', prompt)
        
        # General prompt
        prompt = self.integration._load_prompt('general')
        self.assertIsInstance(prompt, str)
        self.assertIn('{command}', prompt)
        
        # Unknown prompt (should return general)
        prompt = self.integration._load_prompt('unknown')
        self.assertIsInstance(prompt, str)
        self.assertIn('{command}', prompt)
    
    def test_build_prompt(self):
        """Test building a prompt for Claude 3.7."""
        # Device control command
        command = "Turn on the kitchen light"
        prompt = self.integration._build_prompt(command)
        self.assertIsInstance(prompt, str)
        self.assertIn(command, prompt)
        
        # Automation command
        command = "Enable the morning automation"
        prompt = self.integration._build_prompt(command)
        self.assertIsInstance(prompt, str)
        self.assertIn(command, prompt)
        
        # System command
        command = "What is the system status?"
        prompt = self.integration._build_prompt(command)
        self.assertIsInstance(prompt, str)
        self.assertIn(command, prompt)
    
    def test_detect_command_type(self):
        """Test detecting command type."""
        # Device control commands
        self.assertEqual(self.integration._detect_command_type("Turn on the kitchen light"), 'device_control')
        self.assertEqual(self.integration._detect_command_type("Turn off the living room light"), 'device_control')
        self.assertEqual(self.integration._detect_command_type("Set the thermostat to 72 degrees"), 'device_control')
        
        # Automation commands
        self.assertEqual(self.integration._detect_command_type("Enable the morning automation"), 'automation')
        self.assertEqual(self.integration._detect_command_type("Disable the night automation"), 'automation')
        self.assertEqual(self.integration._detect_command_type("Trigger the security automation"), 'automation')
        
        # System commands
        self.assertEqual(self.integration._detect_command_type("What is the system status?"), 'system')
        self.assertEqual(self.integration._detect_command_type("Restart the system"), 'system')
        self.assertEqual(self.integration._detect_command_type("Show system configuration"), 'system')
        
        # General commands
        self.assertEqual(self.integration._detect_command_type("Hello, how are you?"), 'general')
    
    @patch('unitmcp.llm.claude.httpx.AsyncClient')
    async def test_call_claude_api(self, mock_client):
        """Test calling the Claude 3.7 API."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'content': [
                {
                    'text': json.dumps({
                        'command_type': 'device_control',
                        'target': 'kitchen_light',
                        'action': 'activate',
                        'parameters': {}
                    })
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client_instance.post.return_value = mock_response
        
        # Set API key
        self.integration.api_key = "test_api_key"
        
        # Call API
        prompt = "Convert the following command: Turn on the kitchen light"
        result = await self.integration._call_claude_api(prompt)
        
        # Verify
        self.assertIsInstance(result, str)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertEqual(data['target'], 'kitchen_light')
        self.assertEqual(data['action'], 'activate')
        
        # Verify API call
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        self.assertEqual(args[0], "https://api.anthropic.com/v1/messages")
        self.assertIn('headers', kwargs)
        self.assertIn('json', kwargs)
        self.assertEqual(kwargs['json']['messages'][0]['content'], prompt)
    
    @patch('unitmcp.llm.claude.httpx.AsyncClient')
    async def test_call_claude_api_error(self, mock_client):
        """Test calling the Claude 3.7 API with error."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("API error"))
        mock_client_instance.post.return_value = mock_response
        
        # Set API key
        self.integration.api_key = "test_api_key"
        
        # Call API
        prompt = "Convert the following command: Turn on the kitchen light"
        with self.assertRaises(ValueError):
            await self.integration._call_claude_api(prompt)
    
    async def test_call_claude_api_simulation(self):
        """Test calling the Claude 3.7 API in simulation mode."""
        # Ensure no API key
        self.integration.api_key = None
        
        # Call API
        prompt = "Convert the following command: Turn on the kitchen light"
        result = await self.integration._call_claude_api(prompt)
        
        # Verify
        self.assertIsInstance(result, str)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertIn('target', data)
        self.assertIn('action', data)
    
    def test_simulate_claude_response(self):
        """Test simulating a Claude 3.7 response."""
        # Turn on command
        prompt = "Command: Turn on the kitchen light"
        result = self.integration._simulate_claude_response(prompt)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertEqual(data['target'], 'kitchen_light')
        self.assertEqual(data['action'], 'activate')
        
        # Turn off command
        prompt = "Command: Turn off the living room light"
        result = self.integration._simulate_claude_response(prompt)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertEqual(data['target'], 'living_room_light')
        self.assertEqual(data['action'], 'deactivate')
        
        # Set command
        prompt = "Command: Set the thermostat to 72"
        result = self.integration._simulate_claude_response(prompt)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertEqual(data['target'], 'thermostat')
        self.assertEqual(data['action'], 'set_value')
        self.assertEqual(data['parameters']['value'], 72)
        
        # Status command
        prompt = "Command: What is the system status?"
        result = self.integration._simulate_claude_response(prompt)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'system')
        self.assertEqual(data['target'], 'system')
        self.assertEqual(data['action'], 'status')
        
        # Unknown command
        prompt = "Command: Hello, how are you?"
        result = self.integration._simulate_claude_response(prompt)
        data = json.loads(result)
        self.assertEqual(data['command_type'], 'device_control')
        self.assertEqual(data['target'], 'unknown_device')
        self.assertEqual(data['action'], 'unknown_action')
    
    def test_parse_response(self):
        """Test parsing the response from Claude 3.7."""
        # JSON string
        response = '{"command_type": "device_control", "target": "kitchen_light", "action": "activate", "parameters": {}}'
        result = self.integration._parse_response(response)
        self.assertEqual(result['command_type'], 'device_control')
        self.assertEqual(result['target'], 'kitchen_light')
        self.assertEqual(result['action'], 'activate')
        
        # JSON embedded in text
        response = 'Here is the command: {"command_type": "device_control", "target": "kitchen_light", "action": "activate", "parameters": {}}'
        result = self.integration._parse_response(response)
        self.assertEqual(result['command_type'], 'device_control')
        self.assertEqual(result['target'], 'kitchen_light')
        self.assertEqual(result['action'], 'activate')
        
        # Multi-line JSON
        response = '''
        {
            "command_type": "device_control",
            "target": "kitchen_light",
            "action": "activate",
            "parameters": {}
        }
        '''
        result = self.integration._parse_response(response)
        self.assertEqual(result['command_type'], 'device_control')
        self.assertEqual(result['target'], 'kitchen_light')
        self.assertEqual(result['action'], 'activate')
        
        # Invalid JSON
        response = 'This is not JSON'
        result = self.integration._parse_response(response)
        self.assertIn('error', result)
        self.assertIn('raw_response', result)
    
    @patch('unitmcp.llm.claude.ClaudeIntegration._call_claude_api')
    async def test_process_command(self, mock_call_claude_api):
        """Test processing a natural language command."""
        # Setup mock
        mock_call_claude_api.return_value = json.dumps({
            'command_type': 'device_control',
            'target': 'kitchen_light',
            'action': 'activate',
            'parameters': {}
        })
        
        # Process command
        command = "Turn on the kitchen light"
        result = await self.integration.process_command(command)
        
        # Verify
        self.assertEqual(result['command_type'], 'device_control')
        self.assertEqual(result['target'], 'kitchen_light')
        self.assertEqual(result['action'], 'activate')
        
        # Verify API call
        mock_call_claude_api.assert_called_once()
        args, kwargs = mock_call_claude_api.call_args
        self.assertIn(command, args[0])

if __name__ == '__main__':
    unittest.main()
