#!/usr/bin/env python3
"""
Remote Connection Module for UnitMCP

This module provides classes and functions for establishing and managing
remote connections to embedded devices using various protocols.

Supported connection types:
- SSH
- MQTT
- HTTP/HTTPS
- WebSockets
- Serial
- Custom protocols

Classes:
- RemoteConnection: Abstract base class for remote connections
- SSHConnection: SSH connection implementation
- MQTTConnection: MQTT connection implementation
- HTTPConnection: HTTP/HTTPS connection implementation
- WebSocketConnection: WebSocket connection implementation
- SerialConnection: Serial connection implementation
"""

import os
import sys
import time
import asyncio
import logging
import socket
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

# Optional imports that will be loaded on demand
# to avoid unnecessary dependencies
_paramiko_available = False
_paho_mqtt_available = False
_websockets_available = False
_requests_available = False
_serial_available = False

logger = logging.getLogger(__name__)

class RemoteConnection(ABC):
    """
    Abstract base class for remote connections.
    
    This class defines the interface that all connection types must implement.
    """
    
    def __init__(self, host: str, port: Optional[int] = None, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 key_file: Optional[str] = None, timeout: int = 30):
        """
        Initialize a remote connection.
        
        Args:
            host: Hostname or IP address of the remote device
            port: Port number for the connection
            username: Username for authentication
            password: Password for authentication
            key_file: Path to private key file for authentication
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.timeout = timeout
        self._connected = False
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish a connection to the remote device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the remote device.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command on the remote device.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple[int, str, str]: Return code, stdout, and stderr
        """
        pass
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file to the remote device.
        
        Args:
            local_path: Path to the local file
            remote_path: Path where the file should be stored on the remote device
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the remote device.
        
        Args:
            remote_path: Path to the file on the remote device
            local_path: Path where the file should be stored locally
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        pass
    
    @property
    def connected(self) -> bool:
        """
        Check if the connection is established.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected

class SSHConnection(RemoteConnection):
    """
    SSH connection implementation.
    
    This class provides functionality for connecting to remote devices using SSH.
    """
    
    def __init__(self, host: str, port: int = 22, 
                 username: str = "pi", password: Optional[str] = None,
                 key_file: Optional[str] = None, timeout: int = 30):
        """
        Initialize an SSH connection.
        
        Args:
            host: Hostname or IP address of the remote device
            port: SSH port (default: 22)
            username: SSH username (default: "pi")
            password: SSH password
            key_file: Path to private key file
            timeout: Connection timeout in seconds
        """
        super().__init__(host, port, username, password, key_file, timeout)
        self._load_paramiko()
        self._client = None
        self._sftp = None
    
    def _load_paramiko(self):
        """Load the paramiko module if available."""
        global _paramiko_available
        if not _paramiko_available:
            try:
                import paramiko
                _paramiko_available = True
                self._paramiko = paramiko
            except ImportError:
                logger.error("Paramiko is not installed. SSH connections will not be available.")
                logger.error("Install it with: pip install paramiko")
                raise ImportError("Paramiko is required for SSH connections")
    
    async def connect(self) -> bool:
        """
        Establish an SSH connection to the remote device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self._connected:
            return True
        
        try:
            # Create SSH client
            self._client = self._paramiko.SSHClient()
            self._client.set_missing_host_key_policy(self._paramiko.AutoAddPolicy())
            
            # Connect to remote host
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": self.timeout
            }
            
            if self.password:
                connect_kwargs["password"] = self.password
            
            if self.key_file:
                connect_kwargs["key_filename"] = self.key_file
            
            # Run the blocking connect operation in a thread pool
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.connect(**connect_kwargs)
            )
            
            # Open SFTP session
            self._sftp = await asyncio.get_event_loop().run_in_executor(
                None, self._client.open_sftp
            )
            
            self._connected = True
            logger.info(f"SSH connection established to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish SSH connection to {self.host}:{self.port}: {str(e)}")
            self._client = None
            self._sftp = None
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the remote device.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if not self._connected:
            return True
        
        try:
            if self._sftp:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._sftp.close
                )
            
            if self._client:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._client.close
                )
            
            self._connected = False
            self._client = None
            self._sftp = None
            logger.info(f"SSH connection to {self.host}:{self.port} closed")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.host}:{self.port}: {str(e)}")
            return False
    
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command on the remote device via SSH.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple[int, str, str]: Return code, stdout, and stderr
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Execute command
            stdin, stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.exec_command(command, timeout=self.timeout)
            )
            
            # Get output
            stdout_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: stdout.read().decode('utf-8')
            )
            stderr_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: stderr.read().decode('utf-8')
            )
            
            # Get exit status
            exit_status = await asyncio.get_event_loop().run_in_executor(
                None, lambda: stdout.channel.recv_exit_status()
            )
            
            return exit_status, stdout_data, stderr_data
            
        except Exception as e:
            logger.error(f"Error executing command on {self.host}: {str(e)}")
            return -1, "", str(e)
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file to the remote device via SFTP.
        
        Args:
            local_path: Path to the local file
            remote_path: Path where the file should be stored on the remote device
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self._sftp.stat(remote_dir)
                )
            except FileNotFoundError:
                # Create directory structure
                current_dir = ""
                for part in remote_dir.split("/"):
                    if not part:
                        continue
                    current_dir = f"{current_dir}/{part}"
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, lambda: self._sftp.stat(current_dir)
                        )
                    except FileNotFoundError:
                        await asyncio.get_event_loop().run_in_executor(
                            None, lambda: self._sftp.mkdir(current_dir)
                        )
            
            # Upload file
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._sftp.put(local_path, remote_path)
            )
            
            logger.info(f"File uploaded: {local_path} -> {self.host}:{remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading file to {self.host}: {str(e)}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the remote device via SFTP.
        
        Args:
            remote_path: Path to the file on the remote device
            local_path: Path where the file should be stored locally
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)
            
            # Download file
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._sftp.get(remote_path, local_path)
            )
            
            logger.info(f"File downloaded: {self.host}:{remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file from {self.host}: {str(e)}")
            return False

class MQTTConnection(RemoteConnection):
    """
    MQTT connection implementation.
    
    This class provides functionality for connecting to remote devices using MQTT.
    """
    
    def __init__(self, host: str, port: int = 1883, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 client_id: Optional[str] = None, timeout: int = 30):
        """
        Initialize an MQTT connection.
        
        Args:
            host: Hostname or IP address of the MQTT broker
            port: MQTT port (default: 1883)
            username: MQTT username
            password: MQTT password
            client_id: MQTT client ID
            timeout: Connection timeout in seconds
        """
        super().__init__(host, port, username, password, None, timeout)
        self._load_paho_mqtt()
        self.client_id = client_id or f"unitmcp-{os.getpid()}-{time.time()}"
        self._client = None
        self._subscriptions = {}
        self._message_queue = asyncio.Queue()
    
    def _load_paho_mqtt(self):
        """Load the paho-mqtt module if available."""
        global _paho_mqtt_available
        if not _paho_mqtt_available:
            try:
                import paho.mqtt.client as mqtt
                _paho_mqtt_available = True
                self._mqtt = mqtt
            except ImportError:
                logger.error("Paho MQTT is not installed. MQTT connections will not be available.")
                logger.error("Install it with: pip install paho-mqtt")
                raise ImportError("Paho MQTT is required for MQTT connections")
    
    async def connect(self) -> bool:
        """
        Establish an MQTT connection to the broker.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self._connected:
            return True
        
        try:
            # Create MQTT client
            self._client = self._mqtt.Client(client_id=self.client_id)
            
            # Set up callbacks
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            
            # Set authentication if provided
            if self.username and self.password:
                self._client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            connect_future = asyncio.Future()
            self._client.on_connect = lambda client, userdata, flags, rc: connect_future.set_result(rc)
            
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.connect(self.host, self.port, keepalive=60)
            )
            
            # Start the MQTT loop in a separate thread
            self._client.loop_start()
            
            # Wait for connection to be established
            rc = await asyncio.wait_for(connect_future, timeout=self.timeout)
            
            if rc == 0:
                self._connected = True
                logger.info(f"MQTT connection established to {self.host}:{self.port}")
                return True
            else:
                logger.error(f"Failed to connect to MQTT broker: {self._mqtt.connack_string(rc)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to establish MQTT connection to {self.host}:{self.port}: {str(e)}")
            if self._client:
                self._client.loop_stop()
            self._client = None
            self._connected = False
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            # Resubscribe to all topics
            for topic, callback in self._subscriptions.items():
                client.subscribe(topic)
        else:
            logger.error(f"Failed to connect to MQTT broker: {self._mqtt.connack_string(rc)}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        try:
            # Put the message in the queue
            asyncio.run_coroutine_threadsafe(
                self._message_queue.put((msg.topic, msg.payload)),
                asyncio.get_event_loop()
            )
            
            # Call the topic-specific callback if registered
            if msg.topic in self._subscriptions and self._subscriptions[msg.topic]:
                callback = self._subscriptions[msg.topic]
                asyncio.run_coroutine_threadsafe(
                    callback(msg.topic, msg.payload),
                    asyncio.get_event_loop()
                )
        except Exception as e:
            logger.error(f"Error processing MQTT message: {str(e)}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection from {self.host}:{self.port}")
            self._connected = False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the MQTT broker.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if not self._connected:
            return True
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.disconnect
            )
            self._client.loop_stop()
            self._connected = False
            self._client = None
            logger.info(f"MQTT connection to {self.host}:{self.port} closed")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
            return False
    
    async def subscribe(self, topic: str, callback: Optional[Callable[[str, bytes], None]] = None) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to
            callback: Callback function to call when a message is received on this topic
            
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if not self._connected:
            await self.connect()
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.subscribe(topic)
            )
            
            if result[0] == self._mqtt.MQTT_ERR_SUCCESS:
                self._subscriptions[topic] = callback
                logger.info(f"Subscribed to MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to MQTT topic {topic}: {result}")
                return False
            
        except Exception as e:
            logger.error(f"Error subscribing to MQTT topic {topic}: {str(e)}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from an MQTT topic.
        
        Args:
            topic: MQTT topic to unsubscribe from
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        if not self._connected:
            return True
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.unsubscribe(topic)
            )
            
            if result[0] == self._mqtt.MQTT_ERR_SUCCESS:
                if topic in self._subscriptions:
                    del self._subscriptions[topic]
                logger.info(f"Unsubscribed from MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to unsubscribe from MQTT topic {topic}: {result}")
                return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing from MQTT topic {topic}: {str(e)}")
            return False
    
    async def publish(self, topic: str, payload: Union[str, bytes, dict], qos: int = 0, retain: bool = False) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (string, bytes, or dict that will be converted to JSON)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether the message should be retained by the broker
            
        Returns:
            bool: True if publication was successful, False otherwise
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Convert dict to JSON string
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            # Convert string to bytes
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.publish(topic, payload, qos, retain)
            )
            
            if result[0] == self._mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to publish message to MQTT topic {topic}: {result}")
                return False
            
        except Exception as e:
            logger.error(f"Error publishing message to MQTT topic {topic}: {str(e)}")
            return False
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[Tuple[str, bytes]]:
        """
        Receive a message from any subscribed topic.
        
        Args:
            timeout: Maximum time to wait for a message (in seconds)
            
        Returns:
            Optional[Tuple[str, bytes]]: Tuple of (topic, payload) or None if timeout
        """
        try:
            return await asyncio.wait_for(self._message_queue.get(), timeout)
        except asyncio.TimeoutError:
            return None
    
    # These methods are not applicable to MQTT but are required by the interface
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Not applicable for MQTT connections."""
        logger.warning("execute_command is not applicable for MQTT connections")
        return -1, "", "Not supported for MQTT connections"
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Not applicable for MQTT connections."""
        logger.warning("upload_file is not applicable for MQTT connections")
        return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Not applicable for MQTT connections."""
        logger.warning("download_file is not applicable for MQTT connections")
        return False

# Factory function to create the appropriate connection type
def create_connection(connection_type: str, **kwargs) -> RemoteConnection:
    """
    Create a remote connection of the specified type.
    
    Args:
        connection_type: Type of connection to create (ssh, mqtt, http, websocket, serial)
        **kwargs: Connection parameters
        
    Returns:
        RemoteConnection: An instance of the appropriate connection class
        
    Raises:
        ValueError: If the connection type is not supported
    """
    connection_types = {
        "ssh": SSHConnection,
        "mqtt": MQTTConnection,
        # Other connection types can be added here
    }
    
    if connection_type.lower() not in connection_types:
        raise ValueError(f"Unsupported connection type: {connection_type}")
    
    return connection_types[connection_type.lower()](**kwargs)
