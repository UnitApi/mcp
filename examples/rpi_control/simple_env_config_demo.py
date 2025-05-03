#!/usr/bin/env python3
"""
Simple Environment-aware Configuration Demo

This simplified demo shows how to use environment variables in configuration
without requiring a running MCP server. It demonstrates:

1. Loading configuration from YAML with environment variable substitution
2. Creating simulated triggers and actions
3. Running a simple automation sequence
4. Providing clear logging about what's happening

This is ideal for testing configuration changes and environment variable usage
without needing to connect to actual hardware.
"""

import asyncio
import argparse
import logging
import os
import sys
import time
import yaml
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UnitMCP-Demo")

# Import the enhanced ConfigLoader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import ConfigLoader


class SimpleTrigger:
    """Simple trigger class for demonstration purposes."""
    
    def __init__(self, name: str, interval: float, max_count: int = None):
        """Initialize the trigger.
        
        Args:
            name: Trigger name
            interval: Time interval in seconds
            max_count: Maximum number of times to trigger (None for unlimited)
        """
        self.name = name
        self.interval = interval
        self.max_count = max_count
        self.count = 0
        self.callbacks = []
        self.running = False
        self.task = None
        
    def add_callback(self, callback):
        """Add a callback to be executed when the trigger fires."""
        self.callbacks.append(callback)
        
    async def fire(self):
        """Fire the trigger and execute all callbacks."""
        logger.info(f"Trigger '{self.name}' fired")
        self.count += 1
        for callback in self.callbacks:
            await callback()
            
    async def _monitor(self):
        """Monitor for time intervals."""
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval)
            if not self.running:
                break
                
            await self.fire()
            
            if self.max_count is not None and self.count >= self.max_count:
                logger.info(f"Trigger '{self.name}' reached max count ({self.max_count})")
                self.running = False
                break
                
    async def start(self):
        """Start the trigger."""
        logger.info(f"Starting time trigger '{self.name}' (interval: {self.interval}s)")
        self.task = asyncio.create_task(self._monitor())
            
    async def stop(self):
        """Stop the trigger."""
        logger.info(f"Stopping time trigger '{self.name}'")
        self.running = False
        if self.task and not self.task.done():
            await asyncio.sleep(0.1)  # Give the task a chance to exit cleanly
            if not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass


class SimpleAction:
    """Simple action class for demonstration purposes."""
    
    def __init__(self, name: str, type: str = None, **params):
        """Initialize the action.
        
        Args:
            name: Action name
            type: Type of action
            **params: Additional parameters for the action
        """
        self.name = name
        self.action_type = type
        self.params = params
        
    async def execute(self):
        """Execute the action."""
        if self.action_type == "log":
            message = self.params.get("message", "")
            level = self.params.get("level", "info").lower()
            
            if level == "debug":
                logger.debug(message)
            elif level == "info":
                logger.info(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
                
        elif self.action_type == "delay":
            delay = float(self.params.get("delay", 1.0))
            logger.info(f"Executing delay action '{self.name}': {delay}s")
            await asyncio.sleep(delay)
            
        else:
            # For other action types, just log what would happen
            param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
            logger.info(f"Executing {self.action_type} action '{self.name}': {param_str}")


class SimpleSequence:
    """Simple sequence class for demonstration purposes."""
    
    def __init__(self, name: str, actions: List[SimpleAction] = None):
        """Initialize the sequence.
        
        Args:
            name: Sequence name
            actions: List of actions to execute
        """
        self.name = name
        self.actions = actions or []
        
    def add_action(self, action: SimpleAction):
        """Add an action to the sequence."""
        self.actions.append(action)
        
    async def execute(self):
        """Execute all actions in the sequence."""
        logger.info(f"Executing sequence '{self.name}'")
        for action in self.actions:
            await action.execute()
        logger.info(f"Sequence '{self.name}' completed")


class SimpleEnvConfigDemo:
    """Simple environment-aware configuration demo class."""
    
    def __init__(self, config_file: str = None, env_file: str = None):
        """Initialize the demo.
        
        Args:
            config_file: Path to the YAML configuration file
            env_file: Path to the .env file
        """
        # Create the config loader with env file support and automation config type
        self.config_loader = ConfigLoader(config_file, env_file, "automation")
        
        # Load configuration
        self.config = self.config_loader.load_config()
        
        # Set log level from configuration
        log_level = self.config.get("settings", {}).get("log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)
            logger.info(f"Set log level to {log_level}")
            
        # Log configuration information
        name = self.config.get("settings", {}).get("name", "Unnamed Configuration")
        description = self.config.get("settings", {}).get("description", "")
        logger.info(f"Loaded configuration: {name}")
        if description:
            logger.info(f"Description: {description}")
            
        self.triggers = {}
        self.actions = {}
        self.sequences = {}
        self.running = False
        
    def create_triggers(self):
        """Create triggers based on the configuration."""
        for trigger_name, trigger_config in self.config.get("triggers", {}).items():
            trigger_type = trigger_config.get("type")
            
            if trigger_type == "time":
                interval = float(trigger_config.get("interval", 10.0))
                max_count = trigger_config.get("max_count")
                if max_count is not None:
                    max_count = int(max_count)
                    
                self.triggers[trigger_name] = SimpleTrigger(
                    trigger_name, interval, max_count
                )
                logger.info(f"Created time trigger '{trigger_name}' with interval {interval}s")
                
            else:
                # For demo purposes, we'll only implement time triggers
                logger.info(f"Trigger type '{trigger_type}' not implemented in demo, skipping '{trigger_name}'")
                
    def create_actions(self):
        """Create actions based on the configuration."""
        for action_name, action_config in self.config.get("actions", {}).items():
            action_type = action_config.get("type")
            
            # Extract parameters (excluding the type)
            params = {k: v for k, v in action_config.items() if k != "type"}
            
            # Create the action
            self.actions[action_name] = SimpleAction(action_name, action_type, **params)
            logger.info(f"Created {action_type} action '{action_name}'")
                
    def create_sequences(self):
        """Create sequences based on the configuration."""
        for seq_name, seq_config in self.config.get("sequences", {}).items():
            trigger_name = seq_config.get("trigger")
            action_names = seq_config.get("actions", [])
            
            if not trigger_name or trigger_name not in self.triggers:
                logger.warning(f"Invalid trigger '{trigger_name}' for sequence '{seq_name}'")
                continue
                
            # Create the sequence
            sequence = SimpleSequence(seq_name)
            
            # Add actions to the sequence
            for action_name in action_names:
                if action_name in self.actions:
                    sequence.add_action(self.actions[action_name])
                else:
                    logger.warning(f"Invalid action '{action_name}' for sequence '{seq_name}'")
                    
            # Store the sequence
            self.sequences[seq_name] = sequence
            
            # Connect the trigger to the sequence
            trigger = self.triggers[trigger_name]
            trigger.add_callback(sequence.execute)
            
            logger.info(f"Created sequence '{seq_name}' with trigger '{trigger_name}' and {len(action_names)} actions")
            
    async def start_triggers(self):
        """Start all triggers."""
        for trigger_name, trigger in self.triggers.items():
            await trigger.start()
            
    async def stop_triggers(self):
        """Stop all triggers."""
        for trigger_name, trigger in self.triggers.items():
            await trigger.stop()
            
    async def run_demo(self, duration: float = 30.0):
        """Run the demo for the specified duration.
        
        Args:
            duration: Duration to run the demo in seconds
        """
        self.running = True
        try:
            # Create triggers, actions, and sequences
            self.create_triggers()
            self.create_actions()
            self.create_sequences()
            
            # Start all triggers
            await self.start_triggers()
            
            # Wait for the specified duration, providing periodic status updates
            start_time = time.time()
            update_interval = min(5.0, duration / 4)  # Update every 5 seconds or 1/4 of total time
            
            next_update = start_time + update_interval
            while time.time() - start_time < duration and self.running:
                await asyncio.sleep(0.5)  # Check more frequently but don't spam logs
                
                current_time = time.time()
                if current_time >= next_update:
                    elapsed = current_time - start_time
                    remaining = duration - elapsed
                    logger.info(f"Automation running... {elapsed:.1f}s elapsed, {remaining:.1f}s remaining")
                    
                    # Report trigger status
                    for trigger_name, trigger in self.triggers.items():
                        logger.info(f"  - Trigger '{trigger_name}' has fired {trigger.count} times")
                    
                    next_update = current_time + update_interval
            
            logger.info("Automation demo completed")
            
        finally:
            self.running = False
            await self.stop_triggers()


async def main():
    """Main function to run the simple environment-aware configuration demo."""
    parser = argparse.ArgumentParser(
        description="Simple Environment-aware Configuration Demo"
    )
    parser.add_argument("--config", help="Path to YAML configuration file")
    parser.add_argument("--env", help="Path to .env file")
    parser.add_argument("--duration", type=float, default=30.0,
                      help="Duration to run the demo in seconds")
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"Starting Simple Environment-aware Configuration Demo")
    logger.info(f"Config: {args.config or 'default'}")
    logger.info(f"Environment: {args.env or 'default'}")
    logger.info(f"Duration: {args.duration} seconds")
    
    demo = SimpleEnvConfigDemo(
        config_file=args.config,
        env_file=args.env
    )
    
    await demo.run_demo(duration=args.duration)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Demo stopped by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
