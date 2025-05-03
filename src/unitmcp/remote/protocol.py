#!/usr/bin/env python3
"""
Protocol Module for UnitMCP Remote Connections

This module provides protocol implementations for remote device communication.
It includes base protocol classes and specific implementations for different
communication protocols.
"""

import os
import sys
import json
import asyncio
import logging
import socket
import struct
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

logger = logging.getLogger(__name__)

class RemoteProtocol(ABC):
    """
    Abstract base class for remote communication protocols.

    This class defines the interface that all protocol implementations must follow.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize a remote protocol.

        Parameters
        ----------
        timeout : int, optional
            Protocol timeout in seconds, by default 30
        """
        self.timeout = timeout
    
    @abstractmethod
    async def send_message(self, message: Any) -> bool:
        """
        Send a message using the protocol.

        Parameters
        ----------
        message : Any
            Message to send
            
        Returns
        -------
        bool
            True if the message was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[Any]:
        """
        Receive a message using the protocol.
        
        Returns
        -------
        Optional[Any]
            Received message or None if no message is available
        """
        pass


# Alias for backward compatibility
Protocol = RemoteProtocol


class JSONProtocol(RemoteProtocol):
    """
    JSON protocol implementation.
    
    This class provides a protocol implementation that uses JSON for message serialization.
    """
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: int = 30):
        """
        Initialize a JSON protocol.
        
        Args:
            reader: AsyncIO stream reader
            writer: AsyncIO stream writer
            timeout: Protocol timeout in seconds
        """
        super().__init__(timeout)
        self.reader = reader
        self.writer = writer
    
    async def send_message(self, message: Any) -> bool:
        """
        Send a message using JSON serialization.
        
        Args:
            message: Message to send (must be JSON serializable)
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            # Serialize message to JSON
            json_data = json.dumps(message).encode('utf-8')
            
            # Send message length as a 4-byte unsigned integer
            self.writer.write(struct.pack('!I', len(json_data)))
            
            # Send the JSON data
            self.writer.write(json_data)
            await self.writer.drain()
            
            return True
        except Exception as e:
            logger.error(f"Error sending JSON message: {str(e)}")
            return False
    
    async def receive_message(self) -> Optional[Any]:
        """
        Receive a message using JSON deserialization.
        
        Returns:
            Optional[Any]: Received message or None if no message is available
        """
        try:
            # Read message length (4-byte unsigned integer)
            length_data = await asyncio.wait_for(self.reader.readexactly(4), timeout=self.timeout)
            length = struct.unpack('!I', length_data)[0]
            
            # Read the JSON data
            json_data = await asyncio.wait_for(self.reader.readexactly(length), timeout=self.timeout)
            
            # Deserialize JSON
            message = json.loads(json_data.decode('utf-8'))
            
            return message
        except asyncio.IncompleteReadError:
            # Connection closed
            return None
        except asyncio.TimeoutError:
            # Timeout
            logger.warning("Timeout while receiving JSON message")
            return None
        except Exception as e:
            logger.error(f"Error receiving JSON message: {str(e)}")
            return None

class MCPProtocol(RemoteProtocol):
    """
    MCP (Model Context Protocol) protocol implementation.
    
    This class provides a protocol implementation that uses the MCP format for message serialization.
    It extends the JSON protocol with MCP-specific message formats and handling.
    """
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: int = 30):
        """
        Initialize an MCP protocol.
        
        Args:
            reader: AsyncIO stream reader
            writer: AsyncIO stream writer
            timeout: Protocol timeout in seconds
        """
        super().__init__(timeout)
        self.json_protocol = JSONProtocol(reader, writer, timeout)
        self.message_id = 0
        self.pending_responses = {}
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send an MCP message.
        
        Args:
            message: MCP message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        # Add message ID if not present
        if 'id' not in message:
            self.message_id += 1
            message['id'] = self.message_id
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = time.time()
        
        return await self.json_protocol.send_message(message)
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Receive an MCP message.
        
        Returns:
            Optional[Dict[str, Any]]: Received MCP message or None if no message is available
        """
        message = await self.json_protocol.receive_message()
        
        if message is None:
            return None
        
        # Check if this is a response to a pending request
        if 'response_to' in message and message['response_to'] in self.pending_responses:
            # Resolve the pending response
            response_future = self.pending_responses.pop(message['response_to'])
            response_future.set_result(message)
        
        return message
    
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send an MCP request and wait for a response.
        
        Args:
            request: MCP request to send
            
        Returns:
            Optional[Dict[str, Any]]: Response message or None if no response is received
        """
        # Add message ID if not present
        if 'id' not in request:
            self.message_id += 1
            request['id'] = self.message_id
        
        # Create a future for the response
        response_future = asyncio.Future()
        self.pending_responses[request['id']] = response_future
        
        # Send the request
        if not await self.send_message(request):
            # Failed to send request
            self.pending_responses.pop(request['id'])
            return None
        
        try:
            # Wait for the response
            return await asyncio.wait_for(response_future, timeout=self.timeout)
        except asyncio.TimeoutError:
            # Timeout
            self.pending_responses.pop(request['id'])
            logger.warning(f"Timeout waiting for response to request {request['id']}")
            return None

class WebSocketProtocol(RemoteProtocol):
    """
    WebSocket protocol implementation.
    
    This class provides a protocol implementation that uses WebSockets for communication.
    """
    
    def __init__(self, websocket, timeout: int = 30):
        """
        Initialize a WebSocket protocol.
        
        Args:
            websocket: WebSocket connection
            timeout: Protocol timeout in seconds
        """
        super().__init__(timeout)
        self.websocket = websocket
    
    async def send_message(self, message: Any) -> bool:
        """
        Send a message using WebSockets.
        
        Args:
            message: Message to send (must be JSON serializable)
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            # Serialize message to JSON if it's not already a string
            if not isinstance(message, (str, bytes)):
                message = json.dumps(message)
            
            # Send the message
            await self.websocket.send(message)
            
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
            return False
    
    async def receive_message(self) -> Optional[Any]:
        """
        Receive a message using WebSockets.
        
        Returns:
            Optional[Any]: Received message or None if no message is available
        """
        try:
            # Receive the message
            message = await asyncio.wait_for(self.websocket.recv(), timeout=self.timeout)
            
            # Try to parse as JSON
            try:
                return json.loads(message)
            except json.JSONDecodeError:
                # Return as-is if not valid JSON
                return message
        except asyncio.TimeoutError:
            # Timeout
            logger.warning("Timeout while receiving WebSocket message")
            return None
        except Exception as e:
            logger.error(f"Error receiving WebSocket message: {str(e)}")
            return None

class MQTTProtocol(RemoteProtocol):
    """
    MQTT protocol implementation.
    
    This class provides a protocol implementation that uses MQTT for communication.
    """
    
    def __init__(self, mqtt_client, topic_prefix: str = "unitmcp", timeout: int = 30):
        """
        Initialize an MQTT protocol.
        
        Args:
            mqtt_client: MQTT client
            topic_prefix: Prefix for MQTT topics
            timeout: Protocol timeout in seconds
        """
        super().__init__(timeout)
        self.mqtt_client = mqtt_client
        self.topic_prefix = topic_prefix
        self.message_queue = asyncio.Queue()
        self.message_id = 0
        self.pending_responses = {}
    
    async def send_message(self, message: Any, topic: Optional[str] = None) -> bool:
        """
        Send a message using MQTT.
        
        Args:
            message: Message to send (must be JSON serializable)
            topic: MQTT topic to publish to (default: {topic_prefix}/messages)
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if topic is None:
            topic = f"{self.topic_prefix}/messages"
        
        # Add message ID if not present and message is a dict
        if isinstance(message, dict) and 'id' not in message:
            self.message_id += 1
            message['id'] = self.message_id
        
        # Publish the message
        return await self.mqtt_client.publish(topic, message)
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Receive a message from the MQTT queue.
        
        Args:
            timeout: Maximum time to wait for a message (in seconds)
            
        Returns:
            Optional[Any]: Received message or None if no message is available
        """
        try:
            topic, payload = await asyncio.wait_for(self.message_queue.get(), timeout or self.timeout)
            
            # Try to parse as JSON
            try:
                message = json.loads(payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Return as-is if not valid JSON
                message = payload
            
            # Check if this is a response to a pending request
            if isinstance(message, dict) and 'response_to' in message and message['response_to'] in self.pending_responses:
                # Resolve the pending response
                response_future = self.pending_responses.pop(message['response_to'])
                response_future.set_result(message)
            
            return message
        except asyncio.TimeoutError:
            # Timeout
            return None
    
    async def subscribe(self, topic: Optional[str] = None) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to (default: {topic_prefix}/messages/#)
            
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if topic is None:
            topic = f"{self.topic_prefix}/messages/#"
        
        # Define callback for received messages
        async def on_message(topic, payload):
            await self.message_queue.put((topic, payload))
        
        # Subscribe to the topic
        return await self.mqtt_client.subscribe(topic, on_message)
    
    async def send_request(self, request: Dict[str, Any], response_topic: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send an MQTT request and wait for a response.
        
        Args:
            request: Request to send
            response_topic: Topic where the response will be published
                           (default: {topic_prefix}/responses/{request_id})
            
        Returns:
            Optional[Dict[str, Any]]: Response message or None if no response is received
        """
        # Add message ID if not present
        if 'id' not in request:
            self.message_id += 1
            request['id'] = self.message_id
        
        # Set response topic if not specified
        if response_topic is None:
            response_topic = f"{self.topic_prefix}/responses/{request['id']}"
        
        # Add response topic to request
        request['response_topic'] = response_topic
        
        # Create a future for the response
        response_future = asyncio.Future()
        self.pending_responses[request['id']] = response_future
        
        # Subscribe to response topic
        if not await self.subscribe(response_topic):
            # Failed to subscribe
            self.pending_responses.pop(request['id'])
            return None
        
        # Send the request
        if not await self.send_message(request):
            # Failed to send request
            self.pending_responses.pop(request['id'])
            return None
        
        try:
            # Wait for the response
            return await asyncio.wait_for(response_future, timeout=self.timeout)
        except asyncio.TimeoutError:
            # Timeout
            self.pending_responses.pop(request['id'])
            logger.warning(f"Timeout waiting for response to request {request['id']}")
            return None

# Factory function to create the appropriate protocol
def create_protocol(protocol_type: str, **kwargs) -> RemoteProtocol:
    """
    Create a protocol of the specified type.
    
    Args:
        protocol_type: Type of protocol to create (json, mcp, websocket, mqtt)
        **kwargs: Protocol parameters
        
    Returns:
        RemoteProtocol: An instance of the appropriate protocol class
        
    Raises:
        ValueError: If the protocol type is not supported
    """
    protocol_types = {
        "json": JSONProtocol,
        "mcp": MCPProtocol,
        "websocket": WebSocketProtocol,
        "mqtt": MQTTProtocol
    }
    
    if protocol_type.lower() not in protocol_types:
        raise ValueError(f"Unsupported protocol type: {protocol_type}")
    
    return protocol_types[protocol_type.lower()](**kwargs)
