#!/usr/bin/env python3
"""
UnitMCP CLI Example with Natural Language Commands

This example demonstrates how to use the UnitMCP CLI with natural language
commands processed by Claude 3.7.
"""

import asyncio
import logging
import os
import sys
import yaml

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unitmcp.cli.parser import CommandParser
from unitmcp.dsl.integration import DslHardwareIntegration
from unitmcp.llm.claude import ClaudeIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main example function."""
    logger.info("Starting UnitMCP CLI example with natural language commands")
    
    # Create the DSL hardware integration
    integration = DslHardwareIntegration()
    
    # Create the Claude integration
    claude = ClaudeIntegration()
    
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
        
        # Process natural language commands
        logger.info("Processing natural language commands...")
        
        # Example commands
        commands = [
            "Turn on the status LED",
            "Set the traffic light to red",
            "Show system status",
            "Display 'Hello World' on the status display",
            "Turn off all devices"
        ]
        
        for command in commands:
            logger.info(f"Command: {command}")
            
            # Process the command using Claude
            logger.info("Processing with Claude 3.7...")
            result = await claude.process_command(command)
            
            logger.info(f"Processed command: {result}")
            
            # Execute the command if possible
            if 'command_type' in result and 'target' in result and 'action' in result:
                logger.info(f"Executing command: {result['command_type']} - {result['target']} - {result['action']}")
                
                if result['command_type'] == 'device_control':
                    # Get the device
                    device_id = result['target']
                    action = result['action']
                    params = result.get('parameters', {})
                    
                    try:
                        device = integration.get_device(device_id)
                        
                        # Execute the action
                        if hasattr(device, action):
                            method = getattr(device, action)
                            await method(**params)
                            logger.info(f"Command executed successfully")
                        else:
                            logger.error(f"Device {device_id} does not support action {action}")
                    
                    except KeyError:
                        logger.error(f"Device {device_id} not found")
                    except Exception as e:
                        logger.error(f"Error executing command: {e}")
            
            # Wait between commands
            await asyncio.sleep(1)
        
        # Clean up all devices
        logger.info("Cleaning up devices...")
        cleanup_results = await integration.cleanup_devices()
        
    except Exception as e:
        logger.error(f"Error in CLI example: {e}")
        # Clean up devices in case of error
        await integration.cleanup_devices()

if __name__ == "__main__":
    asyncio.run(main())
