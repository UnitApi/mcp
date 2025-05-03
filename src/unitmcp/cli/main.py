#!/usr/bin/env python3
"""
UnitMCP Command Line Interface

This module provides the main entry point for the UnitMCP CLI.
"""

import argparse
import asyncio
import logging
import os
import sys
import yaml
from typing import Dict, Any, List, Optional

from .parser import CommandParser
from .commands import device, automation, system, nl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='UnitMCP Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        '--host', 
        default='localhost',
        help='Host address for the UnitMCP server'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8081,
        help='Port for the UnitMCP server'
    )
    parser.add_argument(
        '--config', 
        help='Path to a configuration file'
    )
    parser.add_argument(
        '--verbose', 
        '-v', 
        action='count', 
        default=0,
        help='Increase verbosity (can be used multiple times)'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Device commands
    device_parser = subparsers.add_parser('device', help='Control hardware devices')
    device.register_commands(device_parser)
    
    # Automation commands
    automation_parser = subparsers.add_parser('automation', help='Manage automations')
    automation.register_commands(automation_parser)
    
    # System commands
    system_parser = subparsers.add_parser('system', help='System management')
    system.register_commands(system_parser)
    
    # Natural language commands
    nl_parser = subparsers.add_parser('nl', help='Natural language commands')
    nl.register_commands(nl_parser)
    
    # Shell mode
    subparsers.add_parser('shell', help='Interactive shell mode')
    
    return parser

async def main() -> int:
    """
    Main entry point for the UnitMCP CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging based on verbosity
    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return 1
    
    # Create command parser
    command_parser = CommandParser(
        host=args.host,
        port=args.port,
        config=config
    )
    
    try:
        # Handle shell mode
        if args.command == 'shell':
            return await run_shell(command_parser)
        
        # Handle other commands
        if args.command is None:
            parser.print_help()
            return 0
        
        # Execute the command
        result = await command_parser.execute(args)
        
        # Print the result
        if isinstance(result, dict):
            if 'error' in result:
                logger.error(f"Error: {result['error']}")
                return 1
            else:
                print(yaml.dump(result, default_flow_style=False))
        else:
            print(result)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose >= 2:
            import traceback
            traceback.print_exc()
        return 1

async def run_shell(command_parser: CommandParser) -> int:
    """
    Run the interactive shell.
    
    Args:
        command_parser: The command parser instance
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    print("UnitMCP Interactive Shell")
    print("Type 'help' for a list of commands, 'exit' to quit")
    
    while True:
        try:
            command = input("unitmcp> ")
            
            if command.lower() in ('exit', 'quit'):
                break
            
            if command.lower() == 'help':
                print("Available commands:")
                print("  device <device_id> <action> [parameters] - Control a device")
                print("  automation load <file> - Load an automation from a file")
                print("  automation list - List all automations")
                print("  system status - Show system status")
                print("  nl <natural language command> - Execute a natural language command")
                print("  exit - Exit the shell")
                continue
            
            # Parse and execute the command
            args = command_parser.parse_shell_command(command)
            if args:
                result = await command_parser.execute(args)
                
                # Print the result
                if isinstance(result, dict):
                    if 'error' in result:
                        print(f"Error: {result['error']}")
                    else:
                        print(yaml.dump(result, default_flow_style=False))
                else:
                    print(result)
        
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
