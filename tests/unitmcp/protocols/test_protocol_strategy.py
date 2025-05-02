#!/usr/bin/env python3
"""
Unit tests for the protocol strategy module.

This module contains tests for the protocol strategy implementations.
"""

import asyncio
import json
import struct
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.protocols.protocol_strategy import (
    ProtocolStrategy,
    JSONProtocolStrategy,
    MCPProtocolStrategy,
    ProtocolContext,
    create_protocol_strategy
)


class TestProtocolStrategy(unittest.TestCase):
    """
    Test cases for the ProtocolStrategy abstract base class.
    """
    
    def test_abstract_methods(self):
        """
        Test that ProtocolStrategy cannot be instantiated directly.
        """
        with self.assertRaises(TypeError):
            ProtocolStrategy()


class TestJSONProtocolStrategy(unittest.TestCase):
    """
    Test cases for the JSONProtocolStrategy class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.reader = MagicMock(spec=asyncio.StreamReader)
        self.writer = MagicMock(spec=asyncio.StreamWriter)
        self.protocol = JSONProtocolStrategy(self.reader, self.writer)
    
    def test_init(self):
        """
        Test initialization of JSONProtocolStrategy.
        """
        self.assertEqual(self.protocol.reader, self.reader)
        self.assertEqual(self.protocol.writer, self.writer)
        self.assertEqual(self.protocol.timeout, 30)
    
    async def async_test_send_message(self):
        """
        Test sending a message.
        """
        message = {"command": "test", "data": "value"}
        
        # Mock the writer.write and writer.drain methods
        self.writer.write = MagicMock()
        self.writer.drain = MagicMock(return_value=asyncio.Future())
        self.writer.drain.return_value.set_result(None)
        
        # Send the message
        result = await self.protocol.send_message(message)
        
        # Check that the message was sent correctly
        self.assertTrue(result)
        self.assertEqual(self.writer.write.call_count, 2)
        
        # Check that the message length was sent first
        length_call = self.writer.write.call_args_list[0]
        length_arg = length_call[0][0]
        self.assertEqual(len(length_arg), 4)  # 4 bytes for the length
        
        # Check that the message was sent second
        message_call = self.writer.write.call_args_list[1]
        message_arg = message_call[0][0]
        self.assertEqual(json.loads(message_arg.decode('utf-8')), message)
        
        # Check that drain was called
        self.writer.drain.assert_called_once()
    
    async def async_test_receive_message(self):
        """
        Test receiving a message.
        """
        message = {"command": "test", "data": "value"}
        message_json = json.dumps(message).encode('utf-8')
        message_length = struct.pack('!I', len(message_json))
        
        # Mock the reader.readexactly method
        self.reader.readexactly = MagicMock()
        self.reader.readexactly.side_effect = [
            asyncio.Future(),  # For the length
            asyncio.Future()   # For the message
        ]
        self.reader.readexactly.side_effect[0].set_result(message_length)
        self.reader.readexactly.side_effect[1].set_result(message_json)
        
        # Receive the message
        result = await self.protocol.receive_message()
        
        # Check that the message was received correctly
        self.assertEqual(result, message)
        self.assertEqual(self.reader.readexactly.call_count, 2)
        
        # Check that the length was read first
        length_call = self.reader.readexactly.call_args_list[0]
        length_arg = length_call[0][0]
        self.assertEqual(length_arg, 4)  # 4 bytes for the length
        
        # Check that the message was read second
        message_call = self.reader.readexactly.call_args_list[1]
        message_arg = message_call[0][0]
        self.assertEqual(message_arg, len(message_json))
    
    async def async_test_receive_message_incomplete_read(self):
        """
        Test receiving a message with an incomplete read.
        """
        # Mock the reader.readexactly method to raise IncompleteReadError
        self.reader.readexactly = MagicMock(side_effect=asyncio.IncompleteReadError(b'', 4))
        
        # Receive the message
        result = await self.protocol.receive_message()
        
        # Check that None was returned
        self.assertIsNone(result)
    
    async def async_test_receive_message_timeout(self):
        """
        Test receiving a message with a timeout.
        """
        # Mock the reader.readexactly method to raise TimeoutError
        self.reader.readexactly = MagicMock(side_effect=asyncio.TimeoutError())
        
        # Receive the message
        result = await self.protocol.receive_message()
        
        # Check that None was returned
        self.assertIsNone(result)
    
    def test_send_message(self):
        """
        Test the send_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_send_message())
        finally:
            loop.close()
    
    def test_receive_message(self):
        """
        Test the receive_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_message())
        finally:
            loop.close()
    
    def test_receive_message_incomplete_read(self):
        """
        Test the receive_message method with an incomplete read.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_message_incomplete_read())
        finally:
            loop.close()
    
    def test_receive_message_timeout(self):
        """
        Test the receive_message method with a timeout.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_message_timeout())
        finally:
            loop.close()


class TestMCPProtocolStrategy(unittest.TestCase):
    """
    Test cases for the MCPProtocolStrategy class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.reader = MagicMock(spec=asyncio.StreamReader)
        self.writer = MagicMock(spec=asyncio.StreamWriter)
        self.protocol = MCPProtocolStrategy(self.reader, self.writer)
    
    def test_init(self):
        """
        Test initialization of MCPProtocolStrategy.
        """
        self.assertIsInstance(self.protocol.json_protocol, JSONProtocolStrategy)
        self.assertEqual(self.protocol.message_id, 0)
        self.assertEqual(self.protocol.pending_responses, {})
    
    async def async_test_send_message(self):
        """
        Test sending a message.
        """
        message = {"command": "test", "data": "value"}
        
        # Mock the json_protocol.send_message method
        self.protocol.json_protocol.send_message = MagicMock(return_value=asyncio.Future())
        self.protocol.json_protocol.send_message.return_value.set_result(True)
        
        # Send the message
        result = await self.protocol.send_message(message)
        
        # Check that the message was sent correctly
        self.assertTrue(result)
        self.protocol.json_protocol.send_message.assert_called_once()
        
        # Check that the message ID and timestamp were added
        sent_message = self.protocol.json_protocol.send_message.call_args[0][0]
        self.assertEqual(sent_message["id"], 1)
        self.assertIn("timestamp", sent_message)
        self.assertEqual(sent_message["command"], "test")
        self.assertEqual(sent_message["data"], "value")
    
    async def async_test_receive_message(self):
        """
        Test receiving a message.
        """
        message = {"id": 1, "command": "test", "data": "value"}
        
        # Mock the json_protocol.receive_message method
        self.protocol.json_protocol.receive_message = MagicMock(return_value=asyncio.Future())
        self.protocol.json_protocol.receive_message.return_value.set_result(message)
        
        # Receive the message
        result = await self.protocol.receive_message()
        
        # Check that the message was received correctly
        self.assertEqual(result, message)
        self.protocol.json_protocol.receive_message.assert_called_once()
    
    async def async_test_receive_response(self):
        """
        Test receiving a response to a pending request.
        """
        request_id = 1
        response = {"id": 2, "response_to": request_id, "result": "success"}
        
        # Create a future for the pending response
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        self.protocol.pending_responses[request_id] = response_future
        
        # Mock the json_protocol.receive_message method
        self.protocol.json_protocol.receive_message = MagicMock(return_value=asyncio.Future())
        self.protocol.json_protocol.receive_message.return_value.set_result(response)
        
        # Receive the message
        result = await self.protocol.receive_message()
        
        # Check that the message was received correctly
        self.assertEqual(result, response)
        self.protocol.json_protocol.receive_message.assert_called_once()
        
        # Check that the pending response was resolved
        self.assertTrue(response_future.done())
        self.assertEqual(response_future.result(), response)
        self.assertEqual(self.protocol.pending_responses, {})
    
    async def async_test_send_request(self):
        """
        Test sending a request and waiting for a response.
        """
        request = {"command": "test", "data": "value"}
        response = {"id": 2, "response_to": 1, "result": "success"}
        
        # Mock the send_message method
        self.protocol.send_message = MagicMock(return_value=asyncio.Future())
        self.protocol.send_message.return_value.set_result(True)
        
        # Create a task to simulate receiving a response
        async def simulate_response():
            # Wait a bit to simulate network delay
            await asyncio.sleep(0.1)
            
            # Get the response future from pending_responses
            response_future = self.protocol.pending_responses[1]
            
            # Set the result
            response_future.set_result(response)
        
        # Start the task
        loop = asyncio.get_running_loop()
        task = loop.create_task(simulate_response())
        
        # Send the request
        result = await self.protocol.send_request(request)
        
        # Wait for the task to complete
        await task
        
        # Check that the request was sent correctly
        self.protocol.send_message.assert_called_once()
        sent_request = self.protocol.send_message.call_args[0][0]
        self.assertEqual(sent_request["id"], 1)
        self.assertEqual(sent_request["command"], "test")
        self.assertEqual(sent_request["data"], "value")
        
        # Check that the response was received correctly
        self.assertEqual(result, response)
        self.assertEqual(self.protocol.pending_responses, {})
    
    async def async_test_send_request_timeout(self):
        """
        Test sending a request with a timeout.
        """
        request = {"command": "test", "data": "value"}
        
        # Mock the send_message method
        self.protocol.send_message = MagicMock(return_value=asyncio.Future())
        self.protocol.send_message.return_value.set_result(True)
        
        # Set a short timeout
        self.protocol.timeout = 0.1
        
        # Send the request
        result = await self.protocol.send_request(request)
        
        # Check that None was returned
        self.assertIsNone(result)
        self.assertEqual(self.protocol.pending_responses, {})
    
    def test_send_message(self):
        """
        Test the send_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_send_message())
        finally:
            loop.close()
    
    def test_receive_message(self):
        """
        Test the receive_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_message())
        finally:
            loop.close()
    
    def test_receive_response(self):
        """
        Test receiving a response to a pending request.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_response())
        finally:
            loop.close()
    
    def test_send_request(self):
        """
        Test the send_request method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_send_request())
        finally:
            loop.close()
    
    def test_send_request_timeout(self):
        """
        Test the send_request method with a timeout.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_send_request_timeout())
        finally:
            loop.close()


class TestProtocolContext(unittest.TestCase):
    """
    Test cases for the ProtocolContext class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.strategy = MagicMock(spec=ProtocolStrategy)
        self.context = ProtocolContext(self.strategy)
    
    def test_init(self):
        """
        Test initialization of ProtocolContext.
        """
        self.assertEqual(self.context.protocol_strategy, self.strategy)
    
    def test_set_strategy(self):
        """
        Test setting a new strategy.
        """
        new_strategy = MagicMock(spec=ProtocolStrategy)
        self.context.set_strategy(new_strategy)
        self.assertEqual(self.context.protocol_strategy, new_strategy)
    
    async def async_test_send_message(self):
        """
        Test sending a message through the context.
        """
        message = {"command": "test", "data": "value"}
        
        # Mock the strategy.send_message method
        self.strategy.send_message = MagicMock(return_value=asyncio.Future())
        self.strategy.send_message.return_value.set_result(True)
        
        # Send the message
        result = await self.context.send_message(message)
        
        # Check that the message was sent correctly
        self.assertTrue(result)
        self.strategy.send_message.assert_called_once_with(message)
    
    async def async_test_receive_message(self):
        """
        Test receiving a message through the context.
        """
        message = {"command": "test", "data": "value"}
        
        # Mock the strategy.receive_message method
        self.strategy.receive_message = MagicMock(return_value=asyncio.Future())
        self.strategy.receive_message.return_value.set_result(message)
        
        # Receive the message
        result = await self.context.receive_message()
        
        # Check that the message was received correctly
        self.assertEqual(result, message)
        self.strategy.receive_message.assert_called_once()
    
    def test_send_message(self):
        """
        Test the send_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_send_message())
        finally:
            loop.close()
    
    def test_receive_message(self):
        """
        Test the receive_message method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_receive_message())
        finally:
            loop.close()


class TestCreateProtocolStrategy(unittest.TestCase):
    """
    Test cases for the create_protocol_strategy function.
    """
    
    @patch('unitmcp.protocols.protocol_strategy.JSONProtocolStrategy')
    def test_create_json_protocol(self, mock_json_protocol):
        """
        Test creating a JSON protocol strategy.
        """
        reader = MagicMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        
        # Create the protocol
        create_protocol_strategy("json", reader=reader, writer=writer)
        
        # Check that the correct protocol was created
        mock_json_protocol.assert_called_once_with(reader, writer, 30)
    
    @patch('unitmcp.protocols.protocol_strategy.MCPProtocolStrategy')
    def test_create_mcp_protocol(self, mock_mcp_protocol):
        """
        Test creating an MCP protocol strategy.
        """
        reader = MagicMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        
        # Create the protocol
        create_protocol_strategy("mcp", reader=reader, writer=writer)
        
        # Check that the correct protocol was created
        mock_mcp_protocol.assert_called_once_with(reader, writer, 30)
    
    def test_create_invalid_protocol(self):
        """
        Test creating an invalid protocol type.
        """
        with self.assertRaises(ValueError):
            create_protocol_strategy("invalid")
    
    def test_create_json_protocol_missing_params(self):
        """
        Test creating a JSON protocol strategy with missing parameters.
        """
        with self.assertRaises(ValueError):
            create_protocol_strategy("json")


if __name__ == '__main__':
    unittest.main()
