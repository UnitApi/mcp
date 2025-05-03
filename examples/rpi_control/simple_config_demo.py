#!/usr/bin/env python3
"""
Simple Configuration-based Automation Demo

This is a simplified version of the config_automation_example.py that doesn't
require a running MCP server. It demonstrates the improved logging and
configuration loading capabilities.
"""

import asyncio
import argparse
import time
import logging
import os
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

class ConfigLoader:
    """Loads automation configuration from YAML files."""
    
    def __init__(self, config_file: str, config_type: str = "automation"):
        """Initialize the configuration loader.
        
        Args:
            config_file: Path to the YAML configuration file
            config_type: Type of configuration (e.g., automation, settings)
        """
        self.config_file = config_file
        self.config_type = config_type
        self.config = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load the configuration from the YAML file.
        
        Returns:
            Dictionary containing the configuration
        """
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

class TimeTrigger:
    """Time-based trigger that fires at specified intervals."""
    
    def __init__(self, name: str, interval: float, max_count: int = None):
        """Initialize the time trigger.
        
        Args:
            name: Trigger name
            interval: Time interval in seconds
            max_count: Maximum number of times to trigger (None for unlimited)
        """
        self.name = name
        self.interval = interval
        self.max_count = max_count
        self.count = 0
        self.running = False
        self.task = None
        self.callbacks = []
        
    def add_callback(self, callback):
        """Add a callback to be executed when the trigger fires."""
        self.callbacks.append(callback)
        
    async def fire(self):
        """Fire the trigger and execute all callbacks."""
        logger.info(f"Trigger '{self.name}' fired")
        for callback in self.callbacks:
            await callback()
            
    async def _monitor(self):
        """Monitor for time intervals."""
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval)
            if not self.running:
                break
                
            self.count += 1
            logger.debug(f"Time trigger '{self.name}' count: {self.count}")
            
            await self.fire()
            
            if self.max_count is not None and self.count >= self.max_count:
                logger.info(f"Time trigger '{self.name}' reached max count ({self.max_count})")
                self.running = False
                break
                
    async def start(self):
        """Start the time trigger."""
        if self.task is None or self.task.done():
            logger.info(f"Starting time trigger '{self.name}' (interval: {self.interval}s)")
            self.task = asyncio.create_task(self._monitor())
            
    async def stop(self):
        """Stop the time trigger."""
        if self.task and not self.task.done():
            logger.info(f"Stopping time trigger '{self.name}'")
            self.running = False
            await asyncio.sleep(0.1)  # Give the task a chance to exit cleanly
            if not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

class Action:
    """Base class for automation actions."""
    
    def __init__(self, name: str):
        """Initialize the action.
        
        Args:
            name: Action name
        """
        self.name = name
        
    async def execute(self):
        """Execute the action."""
        logger.info(f"Executing action '{self.name}'")

class LogAction(Action):
    """Action to log a message."""
    
    def __init__(self, name: str, message: str, level: str = "info"):
        """Initialize the log action.
        
        Args:
            name: Action name
            message: Message to log
            level: Log level ('debug', 'info', 'warning', 'error')
        """
        super().__init__(name)
        self.message = message
        self.level = level.lower()
        
    async def execute(self):
        """Execute the log action."""
        if self.level == "debug":
            logger.debug(self.message)
        elif self.level == "info":
            logger.info(self.message)
        elif self.level == "warning":
            logger.warning(self.message)
        elif self.level == "error":
            logger.error(self.message)
        else:
            # Default to info level
            logger.info(self.message)

class DelayAction(Action):
    """Action to introduce a delay."""
    
    def __init__(self, name: str, delay: float):
        """Initialize the delay action.
        
        Args:
            name: Action name
            delay: Delay time in seconds
        """
        super().__init__(name)
        self.delay = delay
        
    async def execute(self):
        """Execute the delay action."""
        logger.info(f"Executing delay action '{self.name}': {self.delay}s")
        await asyncio.sleep(self.delay)

class Sequence:
    """A sequence of actions to be executed in order."""
    
    def __init__(self, name: str, actions: List[Action] = None):
        """Initialize the sequence.
        
        Args:
            name: Sequence name
            actions: List of actions to execute
        """
        self.name = name
        self.actions = actions or []
        
    def add_action(self, action: Action):
        """Add an action to the sequence.
        
        Args:
            action: Action to add
        """
        self.actions.append(action)
        
    async def execute(self):
        """Execute all actions in the sequence."""
        logger.info(f"Executing sequence '{self.name}'")
        for action in self.actions:
            await action.execute()
        logger.info(f"Sequence '{self.name}' completed")

class SimpleDemo:
    """Simple automation demo class."""
    
    def __init__(self, config_file: str = None):
        """Initialize the automation demo.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        # Create the config loader with automation config type
        self.config_loader = ConfigLoader(config_file, config_type="automation")
        self.config = {}
        self.triggers = {}
        self.actions = {}
        self.sequences = {}
        self.running = False
        
    def load_configuration(self):
        """Load the automation configuration."""
        self.config = self.config_loader.load_config()
        
        # Configure logging level if specified
        settings = self.config.get("settings", {})
        log_level = settings.get("log_level", "").upper()
        if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.setLevel(getattr(logging, log_level))
            logger.info(f"Set log level to {log_level}")
            
        logger.info(f"Loaded configuration: {settings.get('name', 'Unnamed')}")
        logger.info(f"Description: {settings.get('description', 'No description')}")
        
    def create_triggers(self):
        """Create triggers based on the configuration."""
        for trigger_name, trigger_config in self.config.get("triggers", {}).items():
            trigger_type = trigger_config.get("type")
            
            if trigger_type == "time":
                interval = float(trigger_config.get("interval", 10.0))
                max_count = trigger_config.get("max_count")
                if max_count is not None:
                    max_count = int(max_count)
                    
                self.triggers[trigger_name] = TimeTrigger(
                    trigger_name, interval, max_count
                )
                logger.info(f"Created time trigger '{trigger_name}' with interval {interval}s")
                
    def create_actions(self):
        """Create actions based on the configuration."""
        for action_name, action_config in self.config.get("actions", {}).items():
            action_type = action_config.get("type")
            
            if action_type == "log":
                message = action_config.get("message", "")
                level = action_config.get("level", "info")
                
                self.actions[action_name] = LogAction(action_name, message, level)
                logger.info(f"Created log action '{action_name}'")
                
            elif action_type == "delay":
                delay = float(action_config.get("delay", 1.0))
                
                self.actions[action_name] = DelayAction(action_name, delay)
                logger.info(f"Created delay action '{action_name}': {delay}s")
                
    def create_sequences(self):
        """Create sequences based on the configuration."""
        for seq_name, seq_config in self.config.get("sequences", {}).items():
            trigger_name = seq_config.get("trigger")
            action_names = seq_config.get("actions", [])
            
            if not trigger_name or trigger_name not in self.triggers:
                continue
                
            # Create the sequence
            sequence = Sequence(seq_name)
            
            # Add actions to the sequence
            for action_name in action_names:
                if action_name in self.actions:
                    sequence.add_action(self.actions[action_name])
                    
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
        """Run the complete automation demo.
        
        Args:
            duration: Duration to run the demo in seconds
        """
        self.running = True
        try:
            # Load configuration
            self.load_configuration()
            
            # Create triggers, actions, and sequences
            self.create_triggers()
            self.create_actions()
            self.create_sequences()
            
            # Log information about active triggers and sequences
            if self.triggers:
                trigger_names = ", ".join(self.triggers.keys())
                logger.info(f"Active triggers: {trigger_names}")
            else:
                logger.warning("No active triggers configured")
                
            if self.sequences:
                sequence_names = ", ".join(self.sequences.keys())
                logger.info(f"Configured sequences: {sequence_names}")
            else:
                logger.warning("No sequences configured")
                
            # Log what to expect during the waiting period
            for seq_name, sequence in self.sequences.items():
                trigger_name = next((t_name for t_name, trigger in self.triggers.items() 
                                   if sequence in [cb.__self__ for cb in trigger.callbacks]), "unknown")
                
                if trigger_name in self.triggers:
                    trigger = self.triggers[trigger_name]
                    if isinstance(trigger, TimeTrigger):
                        logger.info(f"Sequence '{seq_name}' will run every {trigger.interval} seconds")
                        if trigger.max_count:
                            logger.info(f"  - Will run {trigger.max_count} times maximum")
            
            # Start all triggers
            await self.start_triggers()
            
            logger.info(f"Running automation demo for {duration} seconds...")
            
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
                        if isinstance(trigger, TimeTrigger):
                            logger.info(f"  - Trigger '{trigger_name}' has fired {trigger.count} times")
                    
                    next_update = current_time + update_interval
            
            logger.info("Automation demo completed")
            
        finally:
            self.running = False
            await self.stop_triggers()

async def main():
    """Main function to run the simple demo."""
    parser = argparse.ArgumentParser(description="Simple Configuration-based Automation Demo")
    parser.add_argument("--config", help="Path to YAML configuration file")
    parser.add_argument("--duration", type=float, default=30.0, 
                      help="Duration to run the demo in seconds")
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"Starting Simple Configuration-based Automation Demo")
    logger.info(f"Config: {args.config or 'default'}")
    logger.info(f"Duration: {args.duration} seconds")
    
    demo = SimpleDemo(config_file=args.config)
    await demo.run_demo(duration=args.duration)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Demo stopped by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
