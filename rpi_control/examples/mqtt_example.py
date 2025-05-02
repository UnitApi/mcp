"""
MQTT Bridge Example

This example demonstrates how to use the MQTT bridge for MCP Hardware Access.
"""

import json
import logging
import time
import os
from typing import Dict, Any

import paho.mqtt.client as mqtt
from unitmcp.bridges import MQTTBridge
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_PORT = int(os.getenv('RPI_PORT', '1883'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    """
    Callback for when the client connects to the broker.
    """
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Subscribe to response topics
        client.subscribe("mcp/gpio/setup/+/response")
        client.subscribe("mcp/gpio/control/+/+/response")
        client.subscribe("mcp/gpio/read/+/response")
        client.subscribe("mcp/gpio/write/+/response")
    else:
        logger.error(f"Failed to connect to MQTT broker with code {rc}")

def on_message(client, userdata, msg):
    """
    Callback for when a message is received from the broker.
    """
    logger.info(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

def main():
    """
    Main function to demonstrate the MQTT bridge.
    """
    # Create and start the MQTT bridge
    bridge_config = {
        "broker": RPI_HOST,
        "port": RPI_PORT,
        "client_id": "mcp_mqtt_bridge_example",
        "topic_prefix": "mcp",
        "qos": 1,
    }
    bridge = MQTTBridge(bridge_config)
    
    # Register a device
    bridge.register_device("led1", {
        "type": "led",
        "pin": 17,
        "active_high": True
    })
    
    # Start the bridge
    bridge.start()
    
    # Create a client to interact with the bridge
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(RPI_HOST, RPI_PORT, 60)
    client.loop_start()
    
    try:
        # Example 1: Setup LED
        setup_payload = {"pin": 17, "mode": "output"}
        logger.info("Setting up LED1 via MQTT")
        client.publish("mcp/gpio/setup/17", json.dumps(setup_payload), qos=1)
        time.sleep(1)
        # Example 2: Turn on the LED
        logger.info("Turning on LED1")
        client.publish("mcp/gpio/control/led1/on", json.dumps({}), qos=1)
        time.sleep(1)
        # Example 3: Toggle the LED
        logger.info("Toggling LED1")
        client.publish("mcp/gpio/control/led1/toggle", json.dumps({}), qos=1)
        time.sleep(1)
        # Example 4: Write to the LED
        write_payload = {"value": 1}
        logger.info("Writing value 1 to LED1")
        client.publish("mcp/gpio/write/17", json.dumps(write_payload), qos=1)
        time.sleep(1)
        # Example 5: Turn off the LED
        logger.info("Turning off LED1")
        client.publish("mcp/gpio/control/led1/off", json.dumps({}), qos=1)
        time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        client.loop_stop()
        client.disconnect()
        bridge.stop()
        logger.info("Example completed")

if __name__ == "__main__":
    main()
