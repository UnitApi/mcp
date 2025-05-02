"""
MQTT Bridge for MCP Hardware Access

This module provides an MQTT bridge for MCP Hardware Access, allowing
hardware control through MQTT topics.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Callable, Tuple

import paho.mqtt.client as mqtt

from unitmcp.server import MCPServer

logger = logging.getLogger(__name__)

class MQTTBridge(MCPServer):
    """
    MQTT Bridge for MCP Hardware Access.
    
    This class implements an MQTT bridge for MCP Hardware Access, mapping
    MCP methods to MQTT topics.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the MQTT bridge with the given configuration.
        
        Args:
            config: A dictionary containing configuration parameters for the bridge.
                   Required keys:
                   - broker: MQTT broker address (default: "localhost")
                   - port: MQTT broker port (default: 1883)
                   Optional keys:
                   - username: MQTT username
                   - password: MQTT password
                   - client_id: MQTT client ID (default: "mcp_mqtt_bridge")
                   - topic_prefix: Prefix for all MQTT topics (default: "mcp")
                   - qos: MQTT QoS level (default: 0)
                   - reconnect_delay: Delay between reconnection attempts in seconds (default: 5)
                   - max_reconnect_attempts: Maximum number of reconnection attempts (default: 12)
        """
        super().__init__(config)
        
        # Set default configuration values
        self.config.setdefault("broker", "localhost")
        self.config.setdefault("port", 1883)
        self.config.setdefault("client_id", "mcp_mqtt_bridge")
        self.config.setdefault("topic_prefix", "mcp")
        self.config.setdefault("qos", 0)
        self.config.setdefault("reconnect_delay", 5)
        self.config.setdefault("max_reconnect_attempts", 12)
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=self.config["client_id"])
        
        # Set up authentication if provided
        if "username" in self.config and "password" in self.config:
            self.client.username_pw_set(self.config["username"], self.config["password"])
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Set up topic handlers
        self.topic_handlers = {}
        self._setup_topic_handlers()
        
        # Reconnection state
        self.reconnect_attempt = 0
        self.connected = False
    
    def _setup_topic_handlers(self) -> None:
        """
        Set up the mapping between MQTT topics and MCP methods.
        """
        prefix = self.config["topic_prefix"]
        
        # Map gpio/setup/{pin} to gpio_setup_pin
        setup_topic = f"{prefix}/gpio/setup/+"
        self.topic_handlers[setup_topic] = self._handle_gpio_setup
        
        # Map gpio/control/{device_id}/{action} to gpio_control_led
        control_topic = f"{prefix}/gpio/control/+/+"
        self.topic_handlers[control_topic] = self._handle_gpio_control
        
        # Map gpio/read/{pin} to gpio_read_pin
        read_topic = f"{prefix}/gpio/read/+"
        self.topic_handlers[read_topic] = self._handle_gpio_read
        
        # Map gpio/write/{pin} to gpio_write_pin
        write_topic = f"{prefix}/gpio/write/+"
        self.topic_handlers[write_topic] = self._handle_gpio_write
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """
        Callback for when the client connects to the broker.
        
        Args:
            client: The MQTT client instance.
            userdata: User data passed to the client.
            flags: Response flags from the broker.
            rc: Connection result code.
        """
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.reconnect_attempt = 0
            
            # Subscribe to all topics
            for topic in self.topic_handlers:
                logger.debug(f"Subscribing to topic: {topic}")
                client.subscribe(topic, qos=self.config["qos"])
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """
        Callback for when the client disconnects from the broker.
        
        Args:
            client: The MQTT client instance.
            userdata: User data passed to the client.
            rc: Disconnection result code.
        """
        logger.warning(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False
        
        # If the disconnection was unexpected, try to reconnect
        if rc != 0 and self.running:
            self._reconnect()
    
    def _reconnect(self) -> None:
        """
        Attempt to reconnect to the MQTT broker.
        """
        if self.reconnect_attempt >= self.config["max_reconnect_attempts"]:
            logger.error("Maximum reconnection attempts reached, giving up")
            return
        
        self.reconnect_attempt += 1
        delay = self.config["reconnect_delay"]
        
        logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempt}/{self.config['max_reconnect_attempts']}) in {delay} seconds")
        time.sleep(delay)
        
        try:
            self.client.reconnect()
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            # Try again with exponential backoff
            self.config["reconnect_delay"] = min(delay * 2, 60)
            self._reconnect()
    
    def _on_message(self, client, userdata, msg) -> None:
        """
        Callback for when a message is received from the broker.
        
        Args:
            client: The MQTT client instance.
            userdata: User data passed to the client.
            msg: The received message.
        """
        topic = msg.topic
        logger.debug(f"Received message on topic {topic}")
        
        # Find the handler for this topic
        handler = None
        for pattern, h in self.topic_handlers.items():
            if mqtt.topic_matches_sub(pattern, topic):
                handler = h
                break
        
        if handler is None:
            logger.warning(f"No handler found for topic {topic}")
            return
        
        # Parse the payload as JSON
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON payload: {e}")
            self._publish_error(topic, f"Invalid JSON payload: {str(e)}")
            return
        
        # Call the handler
        try:
            result = handler(topic, payload)
            self._publish_response(topic, result)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self._publish_error(topic, f"Error handling message: {str(e)}")
    
    def _publish_response(self, topic: str, response: Dict[str, Any]) -> None:
        """
        Publish a response to a topic.
        
        Args:
            topic: The original topic.
            response: The response to publish.
        """
        response_topic = f"{topic}/response"
        payload = json.dumps(response)
        logger.debug(f"Publishing response to {response_topic}: {payload}")
        self.client.publish(response_topic, payload, qos=self.config["qos"])
    
    def _publish_error(self, topic: str, error_message: str) -> None:
        """
        Publish an error message to a topic.
        
        Args:
            topic: The original topic.
            error_message: The error message to publish.
        """
        error_topic = f"{topic}/error"
        payload = json.dumps({"status": "error", "message": error_message})
        logger.debug(f"Publishing error to {error_topic}: {payload}")
        self.client.publish(error_topic, payload, qos=self.config["qos"])
    
    def _extract_pin_from_topic(self, topic: str) -> int:
        """
        Extract the pin number from a topic.
        
        Args:
            topic: The topic to extract the pin from.
            
        Returns:
            The pin number.
        """
        parts = topic.split("/")
        return int(parts[-1])
    
    def _extract_device_and_action_from_topic(self, topic: str) -> Tuple[str, str]:
        """
        Extract the device ID and action from a topic.
        
        Args:
            topic: The topic to extract the device ID and action from.
            
        Returns:
            A tuple containing the device ID and action.
        """
        parts = topic.split("/")
        return parts[-2], parts[-1]
    
    def _handle_gpio_setup(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a GPIO setup message.
        
        Args:
            topic: The topic of the message.
            payload: The payload of the message.
            
        Returns:
            The result of the operation.
        """
        pin = self._extract_pin_from_topic(topic)
        mode = payload.get("mode", "input")
        pull_up_down = payload.get("pull_up_down")
        
        return self.gpio_setup_pin(pin, mode, pull_up_down)
    
    def _handle_gpio_control(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a GPIO control message.
        
        Args:
            topic: The topic of the message.
            payload: The payload of the message.
            
        Returns:
            The result of the operation.
        """
        device_id, action = self._extract_device_and_action_from_topic(topic)
        params = payload.get("params", {})
        
        return self.gpio_control_led(device_id, action, params)
    
    def _handle_gpio_read(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a GPIO read message.
        
        Args:
            topic: The topic of the message.
            payload: The payload of the message.
            
        Returns:
            The result of the operation.
        """
        pin = self._extract_pin_from_topic(topic)
        
        return self.gpio_read_pin(pin)
    
    def _handle_gpio_write(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a GPIO write message.
        
        Args:
            topic: The topic of the message.
            payload: The payload of the message.
            
        Returns:
            The result of the operation.
        """
        pin = self._extract_pin_from_topic(topic)
        value = payload.get("value", 0)
        
        return self.gpio_write_pin(pin, value)
    
    def start(self) -> None:
        """
        Start the MQTT bridge.
        """
        if self.running:
            logger.warning("MQTT bridge is already running")
            return
        
        logger.info("Starting MQTT bridge")
        
        try:
            # Connect to the broker
            self.client.connect(self.config["broker"], self.config["port"], 60)
            
            # Start the MQTT loop in a background thread
            self.client.loop_start()
            
            self.running = True
            logger.info(f"MQTT bridge started and connected to {self.config['broker']}:{self.config['port']}")
        except Exception as e:
            logger.error(f"Failed to start MQTT bridge: {e}")
            raise
    
    def stop(self) -> None:
        """
        Stop the MQTT bridge.
        """
        if not self.running:
            logger.warning("MQTT bridge is not running")
            return
        
        logger.info("Stopping MQTT bridge")
        
        try:
            # Stop the MQTT loop
            self.client.loop_stop()
            
            # Disconnect from the broker
            self.client.disconnect()
            
            self.running = False
            self.connected = False
            logger.info("MQTT bridge stopped")
        except Exception as e:
            logger.error(f"Error stopping MQTT bridge: {e}")
            raise
    
    def register_device(self, device_id: str, device_config: Dict[str, Any]) -> None:
        """
        Register a device with the MQTT bridge.
        
        Args:
            device_id: A unique identifier for the device.
            device_config: Configuration parameters for the device.
        """
        logger.info(f"Registering device {device_id} with config {device_config}")
        self.devices[device_id] = device_config
