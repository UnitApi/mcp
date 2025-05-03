#!/usr/bin/env python3
"""
UnitMCP Claude Plugin Quickstart Demo

This script demonstrates the core functionality of the UnitMCP Claude Plugin,
including natural language command processing and hardware control.

Usage:
    SIMULATION=1 VERBOSE=1 python quickstart_demo.py

Environment Variables:
    SIMULATION: Set to 1 to run in simulation mode (default: 1)
    VERBOSE: Set to 1 for verbose logging (default: 0)
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unitmcp.plugin.main import ClaudeUnitMCPPlugin
from unitmcp.plugin.core.dsl_integration import DslIntegration

# Configure logging
verbose = os.environ.get("VERBOSE", "0") == "1"
log_level = logging.DEBUG if verbose else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("quickstart_demo")

# Sample device configuration
SAMPLE_CONFIG = """
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
    name: Info Display
  traffic_light1:
    type: traffic_light
    red_pin: 17
    yellow_pin: 27
    green_pin: 22
    name: Main Traffic Light
"""

# Sample natural language commands
SAMPLE_COMMANDS = [
    "Turn on the LED",
    "Make the traffic light show green",
    "Show 'Hello World' on the display",
    "Turn off the LED",
    "Blink the LED at 2 Hz",
    "Press the button",
    "Make the traffic light cycle through all colors"
]

async def run_demo():
    """Run the UnitMCP Claude Plugin demo."""
    logger.info("Starting UnitMCP Claude Plugin demo")
    
    # Initialize the plugin
    plugin = ClaudeUnitMCPPlugin()
    await plugin.initialize()
    
    # Load device configuration
    dsl = DslIntegration(simulation_mode=True)
    result = await dsl.load_config(SAMPLE_CONFIG)
    
    if result.get("status") == "error":
        logger.error(f"Failed to load configuration: {result.get('error')}")
        return
    
    logger.info(f"Loaded configuration with {len(result.get('devices', {}))} devices")
    
    # Initialize devices
    await dsl.initialize_devices()
    
    # Process sample commands
    conversation_id = "demo_conversation"
    user_id = "demo_user"
    
    logger.info("\n" + "="*50)
    logger.info("Processing sample commands")
    logger.info("="*50)
    
    for i, command in enumerate(SAMPLE_COMMANDS):
        logger.info(f"\nCommand {i+1}: {command}")
        
        # Create a query object
        query = {
            "text": command,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
        # Process the query
        response = await plugin.process_query(query)
        
        if response.get("has_hardware_intent"):
            logger.info("Hardware intent detected")
            
            # Print the results
            for result in response.get("results", []):
                if result.get("status") == "success":
                    parsed = result.get("parsed_command", {})
                    logger.info(f"Executed: {parsed.get('device_type')}.{parsed.get('device_id')}.{parsed.get('action')}({parsed.get('parameters')})")
                else:
                    logger.error(f"Error: {result.get('error')}")
            
            # Print the response
            logger.info(f"Response: {response.get('response')}")
        else:
            logger.info("No hardware intent detected")
        
        # Add a delay between commands
        await asyncio.sleep(1)
    
    logger.info("\n" + "="*50)
    logger.info("Demo completed")
    logger.info("="*50)

def main():
    """Main entry point."""
    # Set simulation mode
    if "SIMULATION" not in os.environ:
        os.environ["SIMULATION"] = "1"
    
    # Run the demo
    asyncio.run(run_demo())

if __name__ == "__main__":
    main()
