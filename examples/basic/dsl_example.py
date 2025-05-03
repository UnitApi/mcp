#!/usr/bin/env python3
"""
UnitMCP DSL Integration Example

This example demonstrates how to use the DSL integration to load
device configurations and control hardware devices.
"""

import asyncio
import logging
import os
import sys
import yaml

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.dsl.integration import DslHardwareIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main example function."""
    logger.info("Starting UnitMCP DSL integration example")
    
    # Create the DSL hardware integration
    integration = DslHardwareIntegration()
    
    try:
        # Load the device configuration from YAML file
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        config_path = os.path.join(project_root, 'configs', 'yaml', 'devices', 'default.yaml')
        logger.info(f"Loading configuration from {config_path}")
        
        result = await integration.load_config_file(config_path)
        devices = result['devices']
        
        logger.info(f"Loaded {len(devices)} devices:")
        for device_id in devices:
            logger.info(f"  - {device_id}")
        
        # Initialize all devices
        logger.info("Initializing devices...")
        init_results = await integration.initialize_devices()
        
        for device_id, success in init_results.items():
            logger.info(f"  - {device_id}: {'Success' if success else 'Failed'}")
        
        # Example: Control the LED device
        logger.info("Controlling the LED device...")
        led = integration.get_device('status_led')
        
        logger.info("Activating LED")
        await led.activate()
        await asyncio.sleep(1)
        
        logger.info("Setting LED brightness to 50%")
        if hasattr(led, 'set_brightness'):
            await led.set_brightness(0.5)
        await asyncio.sleep(1)
        
        logger.info("Deactivating LED")
        await led.deactivate()
        await asyncio.sleep(1)
        
        # Example: Control the traffic light
        logger.info("Controlling the traffic light...")
        traffic_light = integration.get_device('traffic_light')
        
        logger.info("Setting traffic light to red")
        await traffic_light.set_state('red')
        await asyncio.sleep(1)
        
        logger.info("Setting traffic light to yellow")
        await traffic_light.set_state('yellow')
        await asyncio.sleep(1)
        
        logger.info("Setting traffic light to green")
        await traffic_light.set_state('green')
        await asyncio.sleep(1)
        
        # Example: Execute a command using the DSL integration
        logger.info("Executing a command through the DSL integration...")
        command = {
            'device': 'status_display',
            'action': 'write_text',
            'parameters': {
                'text': 'Hello, UnitMCP!',
                'line': 0
            }
        }
        
        result = await integration.execute_command(command)
        logger.info(f"Command result: {result}")
        
        # Clean up all devices
        logger.info("Cleaning up devices...")
        cleanup_results = await integration.cleanup_devices()
        
        for device_id, success in cleanup_results.items():
            logger.info(f"  - {device_id}: {'Success' if success else 'Failed'}")
        
    except Exception as e:
        logger.error(f"Error in DSL example: {e}")
        # Clean up devices in case of error
        await integration.cleanup_devices()

if __name__ == "__main__":
    asyncio.run(main())
