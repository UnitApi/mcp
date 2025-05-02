#!/usr/bin/env python3
"""
Protocol Strategy Module for UnitMCP

This module implements the Strategy Pattern for communication protocols in UnitMCP.
It provides a unified interface for different protocol implementations and a context
class that manages protocol selection and usage.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

logger = logging.getLogger(__name__)


class ProtocolStrategy(ABC):
    """
    Abstract base class for protocol strategies.
    
    This class defines the interface that all protocol strategy implementations must follow.
    It implements the Strategy Pattern for communication protocols.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize a protocol strategy.
        
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


class JSONProtocolStrategy(ProtocolStrategy):
    """
    JSON protocol strategy implementation.
    
    This class provides a protocol implementation that uses JSON for message serialization.
    """
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: int = 30):
        """
        Initialize a JSON protocol strategy.
        
        Parameters
        ----------
        reader : asyncio.StreamReader
            AsyncIO stream reader
        writer : asyncio.StreamWriter
            AsyncIO stream writer
        timeout : int, optional
            Protocol timeout in seconds, by default 30
        """
        super().__init__(timeout)
        self.reader = reader
        self.writer = writer
    
    async def send_message(self, message: Any) -> bool:
        """
        Send a message using JSON serialization.
        
        Parameters
        ----------
        message : Any
            Message to send (must be JSON serializable)
            
        Returns
        -------
        bool
            True if the message was sent successfully, False otherwise
        """
        import json
        import struct
        
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
        
        Returns
        -------
        Optional[Any]
            Received message or None if no message is available
        """
        import json
        import struct
        
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


class MCPProtocolStrategy(ProtocolStrategy):
    """
    MCP (Model Context Protocol) protocol strategy implementation.
    
    This class provides a protocol implementation that uses the MCP format for message serialization.
    It extends the JSON protocol with MCP-specific message formats and handling.
    """
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: int = 30):
        """
        Initialize an MCP protocol strategy.
        
        Parameters
        ----------
        reader : asyncio.StreamReader
            AsyncIO stream reader
        writer : asyncio.StreamWriter
            AsyncIO stream writer
        timeout : int, optional
            Protocol timeout in seconds, by default 30
        """
        super().__init__(timeout)
        self.json_protocol = JSONProtocolStrategy(reader, writer, timeout)
        self.message_id = 0
        self.pending_responses = {}
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send an MCP message.
        
        Parameters
        ----------
        message : Dict[str, Any]
            MCP message to send
            
        Returns
        -------
        bool
            True if the message was sent successfully, False otherwise
        """
        import time
        
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
        
        Returns
        -------
        Optional[Dict[str, Any]]
            Received MCP message or None if no message is available
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
        
        Parameters
        ----------
        request : Dict[str, Any]
            Request to send
            
        Returns
        -------
        Optional[Dict[str, Any]]
            Response message or None if no response is received
        """
        # Add request ID if not present
        if 'id' not in request:
            self.message_id += 1
            request['id'] = self.message_id
        
        # Create a future for the response
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        self.pending_responses[request['id']] = response_future
        
        # Send the request
        if not await self.send_message(request):
            self.pending_responses.pop(request['id'])
            return None
        
        # Wait for the response
        try:
            response = await asyncio.wait_for(response_future, timeout=self.timeout)
            return response
        except asyncio.TimeoutError:
            self.pending_responses.pop(request['id'])
            logger.warning(f"Timeout waiting for response to request {request['id']}")
            return None


class ProtocolContext:
    """
    Protocol context class.
    
    This class manages protocol strategies and provides a unified interface for using them.
    It implements the Strategy Pattern for communication protocols.
    """
    
    def __init__(self, protocol_strategy: ProtocolStrategy):
        """
        Initialize a protocol context.
        
        Parameters
        ----------
        protocol_strategy : ProtocolStrategy
            Protocol strategy to use
        """
        self.protocol_strategy = protocol_strategy
    
    def set_strategy(self, protocol_strategy: ProtocolStrategy):
        """
        Set the protocol strategy.
        
        Parameters
        ----------
        protocol_strategy : ProtocolStrategy
            Protocol strategy to use
        """
        self.protocol_strategy = protocol_strategy
    
    async def send_message(self, message: Any) -> bool:
        """
        Send a message using the current protocol strategy.
        
        Parameters
        ----------
        message : Any
            Message to send
            
        Returns
        -------
        bool
            True if the message was sent successfully, False otherwise
        """
        return await self.protocol_strategy.send_message(message)
    
    async def receive_message(self) -> Optional[Any]:
        """
        Receive a message using the current protocol strategy.
        
        Returns
        -------
        Optional[Any]
            Received message or None if no message is available
        """
        return await self.protocol_strategy.receive_message()


# Factory function to create the appropriate protocol strategy
def create_protocol_strategy(protocol_type: str, **kwargs) -> ProtocolStrategy:
    """
    Create a protocol strategy of the specified type.
    
    Parameters
    ----------
    protocol_type : str
        Type of protocol strategy to create (json, mcp, websocket, mqtt)
    **kwargs
        Protocol strategy parameters
    
    Returns
    -------
    ProtocolStrategy
        An instance of the appropriate protocol strategy class
    
    Raises
    ------
    ValueError
        If the protocol type is not supported
    """
    if protocol_type == "json":
        if "reader" not in kwargs or "writer" not in kwargs:
            raise ValueError("JSON protocol requires reader and writer parameters")
        return JSONProtocolStrategy(kwargs["reader"], kwargs["writer"], kwargs.get("timeout", 30))
    elif protocol_type == "mcp":
        if "reader" not in kwargs or "writer" not in kwargs:
            raise ValueError("MCP protocol requires reader and writer parameters")
        return MCPProtocolStrategy(kwargs["reader"], kwargs["writer"], kwargs.get("timeout", 30))
    else:
        raise ValueError(f"Unsupported protocol type: {protocol_type}")
