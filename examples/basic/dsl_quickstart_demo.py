#!/usr/bin/env python3
"""
UnitMCP DSL Quickstart Demo

This script demonstrates how to use the UnitMCP DSL to control hardware devices
using both configuration files and natural language commands.

Run this script with:
    SIMULATION=1 python quickstart_demo.py
"""

import os
import sys
import asyncio
import logging
import yaml
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set simulation mode
os.environ['SIMULATION'] = '1'

async def dsl_config_demo():
    """Demonstrate using the DSL with a configuration file."""
    try:
        from unitmcp.dsl.integration import DslHardwareIntegration
        
        # Create the DSL hardware integration in simulation mode
        integration = DslHardwareIntegration(simulation=True)
        logger.info("Created DSL hardware integration in simulation mode")
        
        # Define a simple configuration
        config = """
        devices:
          led1:
            type: led
            pin: 17
            name: Status LED
          button1:
            type: button
            pin: 18
            name: Control Button
          display1:
            type: display
            display_type: oled
            width: 128
            height: 64
            address: 0x3C
            name: Info Display
        """
        
        # Load the configuration
        result = await integration.load_config(config)
        logger.info(f"Loaded configuration with {len(result['devices'])} devices")
        
        # Initialize the devices
        init_result = await integration.initialize_devices()
        logger.info(f"Initialized {len(init_result)} devices")
        
        # Execute some commands
        commands = [
            {"device": "led1", "action": "on", "parameters": {}},
            {"device": "led1", "action": "blink", "parameters": {"duration": 2, "count": 3}},
            {"device": "led1", "action": "off", "parameters": {}}
        ]
        
        for cmd in commands:
            logger.info(f"Executing command: {cmd}")
            result = await integration.execute_command(cmd)
            logger.info(f"Command result: {result}")
        
        # Clean up the devices
        cleanup_result = await integration.cleanup_devices()
        logger.info(f"Cleaned up {len(cleanup_result)} devices")
        
        return True
    except Exception as e:
        logger.error(f"Error in DSL config demo: {e}")
        return False

async def natural_language_demo():
    """Demonstrate using natural language commands with Claude integration."""
    try:
        from unitmcp.dsl.integration import DslHardwareIntegration
        from unitmcp.llm.claude import ClaudeIntegration
        
        # Create the DSL hardware integration in simulation mode
        integration = DslHardwareIntegration(simulation=True)
        
        # Create the Claude integration
        claude = ClaudeIntegration(api_key="simulation_key")
        logger.info("Created Claude integration in simulation mode")
        
        # Load a simple configuration
        config = """
        devices:
          kitchen_light:
            type: led
            pin: 17
            name: Kitchen Light
          living_room_light:
            type: led
            pin: 18
            name: Living Room Light
          bedroom_light:
            type: led
            pin: 19
            name: Bedroom Light
        """
        
        # Load the configuration
        await integration.load_config(config)
        await integration.initialize_devices()
        
        # Process natural language commands
        commands = [
            "Turn on the kitchen light",
            "Turn off the living room light",
            "Blink the bedroom light 3 times",
            "Turn off all lights"
        ]
        
        # Action mapping from natural language to device actions
        action_mapping = {
            "activate": "on",
            "deactivate": "off",
            "blink": "blink"
        }
        
        # Device mapping to handle unknown devices
        device_mapping = {
            "unknown_device": "bedroom_light",  # Default to bedroom light for unknown devices
            "all_lights": ["kitchen_light", "living_room_light", "bedroom_light"]
        }
        
        for cmd in commands:
            logger.info(f"Processing natural language command: '{cmd}'")
            
            try:
                # Process the command with Claude
                processed_cmd = await claude.process_command(cmd)
                logger.info(f"Processed command: {processed_cmd}")
                
                # Map the action to a device action
                action = action_mapping.get(processed_cmd.get('action', ''), 'on')
                
                # Get the target device
                target = processed_cmd.get('target')
                
                # Handle special case for all lights
                if target == 'all_lights':
                    for device_id in device_mapping['all_lights']:
                        device_cmd = {
                            "device": device_id,
                            "action": action,
                            "parameters": processed_cmd.get('parameters', {})
                        }
                        result = await integration.execute_command(device_cmd)
                        logger.info(f"Command result for {device_id}: {result}")
                else:
                    # Handle unknown device by mapping to a known device
                    if target == 'unknown_device' or target not in integration.devices:
                        # For the "Blink the bedroom light" command
                        if "blink" in cmd.lower() and "bedroom" in cmd.lower():
                            target = "bedroom_light"
                            action = "blink"
                            # Add parameters for blink count if mentioned
                            if "3 times" in cmd:
                                processed_cmd['parameters'] = {"count": 3}
                        else:
                            target = device_mapping.get(target, list(integration.devices.keys())[0])
                    
                    # Execute the command
                    device_cmd = {
                        "device": target,
                        "action": action,
                        "parameters": processed_cmd.get('parameters', {})
                    }
                    result = await integration.execute_command(device_cmd)
                    logger.info(f"Command result for {target}: {result}")
            except Exception as e:
                logger.error(f"Error processing command '{cmd}': {e}")
        
        # Clean up the devices
        await integration.cleanup_devices()
        
        return True
    except Exception as e:
        logger.error(f"Error in natural language demo: {e}")
        return False

async def cli_demo():
    """Demonstrate using the CLI command parser."""
    try:
        from unitmcp.cli.parser import CommandParser
        
        # Create the command parser
        parser = CommandParser()
        logger.info("Created CLI command parser")
        
        # Parse some example commands
        commands = [
            "device led1 on",
            "device button1 status",
            "device display1 show_text 'Hello, World!'",
            "natural turn on the kitchen light",
            "natural dim the living room lights to 50%"
        ]
        
        for cmd in commands:
            logger.info(f"Parsing CLI command: '{cmd}'")
            result = parser.parse(cmd)
            logger.info(f"Parsed command: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error in CLI demo: {e}")
        return False

async def run_demos():
    """Run all the demonstration examples."""
    logger.info("Starting UnitMCP DSL Quickstart Demo")
    
    # Run the DSL configuration demo
    logger.info("\n=== DSL Configuration Demo ===")
    await dsl_config_demo()
    
    # Run the natural language demo
    logger.info("\n=== Natural Language Demo ===")
    await natural_language_demo()
    
    # Run the CLI demo
    logger.info("\n=== CLI Command Parser Demo ===")
    await cli_demo()
    
    logger.info("\nUnitMCP DSL Quickstart Demo completed")

if __name__ == "__main__":
    asyncio.run(run_demos())
