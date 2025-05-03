#!/usr/bin/env python3
"""
Basic Orchestrator Example

This example demonstrates how to use the Orchestrator to list and run examples.
"""

import sys
import logging
from unitmcp.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the basic orchestrator example."""
    # Create an Orchestrator instance
    orchestrator = Orchestrator()
    
    # Get all available examples
    examples = orchestrator.get_examples()
    
    # Print the list of examples
    print("\nAvailable examples:")
    print("=" * 50)
    for name, info in examples.items():
        description = info.get("description", "")
        if len(description) > 60:
            description = description[:57] + "..."
        
        has_runner = "✓" if info.get("has_runner") else " "
        has_server = "✓" if info.get("has_server") else " "
        
        print(f"{name:<20} | Runner: [{has_runner}] | Server: [{has_server}]")
        print(f"  {description}")
        print("-" * 50)
    
    # Run an example if specified
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        
        if example_name not in examples:
            logger.error(f"Example '{example_name}' not found")
            sys.exit(1)
        
        print(f"\nRunning example: {example_name}")
        runner_info = orchestrator.run_example(example_name, simulation=True)
        
        if runner_info["status"] == "running":
            print(f"Runner started with ID: {runner_info['id']}")
            
            # Wait for user input to stop the runner
            input("\nPress Enter to stop the runner...")
            
            # Stop the runner
            orchestrator.stop_runner(runner_info["id"])
            print(f"Runner stopped")
        else:
            logger.error(f"Failed to start runner: {runner_info.get('error', 'Unknown error')}")
            sys.exit(1)

if __name__ == "__main__":
    main()
