"""
Natural Language Commands for UnitMCP CLI

This module provides natural language command processing for the UnitMCP CLI.
"""

import argparse
from typing import Dict, Any

def register_commands(parser: argparse.ArgumentParser) -> None:
    """
    Register natural language commands with the argument parser.
    
    Args:
        parser: The argument parser
    """
    parser.add_argument(
        'command',
        nargs='+',
        help='Natural language command'
    )

async def handle_command(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Handle a natural language command.
    
    Args:
        args: Command arguments
    
    Returns:
        Command result
    """
    # This is handled by the command parser
    pass
