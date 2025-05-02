#!/usr/bin/env python3
"""
Unit tests for the remote protocol module.
"""

import os
import sys
import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.remote.protocol import (
    Protocol,
    JSONProtocol,
    MCPProtocol
)

class TestProtocol(unittest.TestCase):
    """Test cases for the Protocol base class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        protocol = Protocol()
        
        with self.assertRaises(NotImplementedError):
            protocol.serialize({"test": "data"})
        
        with self.assertRaises(NotImplementedError):
            protocol.deserialize('{"test": "data"}')
        
        with self.assertRaises(NotImplementedError):
            protocol.validate({"test": "data"})


class TestJSONProtocol(unittest.TestCase):
    """Test cases for the JSONProtocol class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.protocol = JSONProtocol()
        self.test_data = {"command": "test", "args": ["arg1", "arg2"], "options": {"opt1": True}}
    
    def test_serialize(self):
        """Test serializing data to JSON."""
        # Serialize the test data
        serialized = self.protocol.serialize(self.test_data)
        
        # Check that the serialized data is a string
        self.assertIsInstance(serialized, str)
        
        # Check that the serialized data can be parsed as JSON
        parsed = json.loads(serialized)
        self.assertEqual(parsed, self.test_data)
    
    def test_deserialize(self):
        """Test deserializing JSON data."""
        # Serialize the test data
        serialized = json.dumps(self.test_data)
        
        # Deserialize the data
        deserialized = self.protocol.deserialize(serialized)
        
        # Check that the deserialized data matches the original
        self.assertEqual(deserialized, self.test_data)
    
    def test_deserialize_invalid(self):
        """Test deserializing invalid JSON data."""
        # Try to deserialize invalid JSON
        with self.assertRaises(json.JSONDecodeError):
            self.protocol.deserialize("invalid json")
    
    def test_validate_valid(self):
        """Test validating valid data."""
        # Validate the test data
        self.assertTrue(self.protocol.validate(self.test_data))
    
    def test_validate_invalid(self):
        """Test validating invalid data."""
        # Validate invalid data (not a dict)
        self.assertFalse(self.protocol.validate("not a dict"))
        
        # Validate invalid data (missing required fields)
        self.assertFalse(self.protocol.validate({}))


class TestMCPProtocol(unittest.TestCase):
    """Test cases for the MCPProtocol class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.protocol = MCPProtocol()
        self.test_data = {
            "type": "command",
            "target": "device1",
            "action": "set_pin",
            "params": {
                "pin": 13,
                "value": 1
            },
            "id": "cmd123"
        }
    
    def test_serialize(self):
        """Test serializing data to MCP format."""
        # Serialize the test data
        serialized = self.protocol.serialize(self.test_data)
        
        # Check that the serialized data is a string
        self.assertIsInstance(serialized, str)
        
        # Check that the serialized data can be parsed as JSON
        parsed = json.loads(serialized)
        self.assertEqual(parsed, self.test_data)
    
    def test_deserialize(self):
        """Test deserializing MCP data."""
        # Serialize the test data
        serialized = json.dumps(self.test_data)
        
        # Deserialize the data
        deserialized = self.protocol.deserialize(serialized)
        
        # Check that the deserialized data matches the original
        self.assertEqual(deserialized, self.test_data)
    
    def test_validate_command(self):
        """Test validating a command message."""
        # Validate the test data (command)
        self.assertTrue(self.protocol.validate(self.test_data))
    
    def test_validate_response(self):
        """Test validating a response message."""
        # Create a response message
        response = {
            "type": "response",
            "target": "device1",
            "status": "success",
            "data": {"pin": 13, "value": 1},
            "id": "cmd123"
        }
        
        # Validate the response
        self.assertTrue(self.protocol.validate(response))
    
    def test_validate_event(self):
        """Test validating an event message."""
        # Create an event message
        event = {
            "type": "event",
            "source": "device1",
            "event": "pin_change",
            "data": {"pin": 13, "value": 1},
            "timestamp": 1620000000
        }
        
        # Validate the event
        self.assertTrue(self.protocol.validate(event))
    
    def test_validate_invalid(self):
        """Test validating invalid messages."""
        # Validate invalid data (not a dict)
        self.assertFalse(self.protocol.validate("not a dict"))
        
        # Validate invalid data (missing required fields)
        self.assertFalse(self.protocol.validate({}))
        
        # Validate invalid data (invalid type)
        invalid_type = self.test_data.copy()
        invalid_type["type"] = "invalid"
        self.assertFalse(self.protocol.validate(invalid_type))
        
        # Validate invalid data (missing required fields for type)
        invalid_command = {"type": "command", "target": "device1"}
        self.assertFalse(self.protocol.validate(invalid_command))
        
        invalid_response = {"type": "response", "target": "device1"}
        self.assertFalse(self.protocol.validate(invalid_response))
        
        invalid_event = {"type": "event", "source": "device1"}
        self.assertFalse(self.protocol.validate(invalid_event))


if __name__ == '__main__':
    unittest.main()
