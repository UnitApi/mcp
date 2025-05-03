#!/usr/bin/env python3
"""
UnitMCP Git Runner Example

This example demonstrates how to use the Git Runner to clone and run applications
from Git repositories.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
sys.path.insert(0, project_root)

# Import the Git Runner
from examples.runner.git_runner import GitRunner
from examples.runner.git_runner_integration import GitRunnerIntegration


async def run_simple_example():
    """Run a simple example using the Git Runner."""
    print("=== Running Simple Git Runner Example ===")
    
    # Example repository URL (a simple static HTML site)
    git_url = "https://github.com/bradtraversy/50projects50days.git"
    
    # Create a temporary directory for the repository
    import tempfile
    target_dir = tempfile.mkdtemp()
    
    try:
        # Create and run the Git Runner
        runner = GitRunner(
            git_url=git_url,
            target_dir=target_dir,
            branch="master",  # Specify the branch to clone
            interactive=True,  # Enable interactive mode
            auto_start=True,   # Automatically start the application
            log_level="INFO"   # Set log level
        )
        
        # Run the Git Runner
        exit_code = await runner.run()
        
        print(f"Git Runner exited with code: {exit_code}")
        print(f"Repository cloned to: {target_dir}")
        
        # Keep the application running for a while
        print("Application is running. Press Ctrl+C to stop...")
        try:
            await asyncio.sleep(60)  # Run for 60 seconds
        except asyncio.CancelledError:
            pass
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(target_dir)


async def run_unitmcp_example():
    """Run an example using the Git Runner with UnitMCP integration."""
    print("=== Running UnitMCP Git Runner Example ===")
    
    # Example repository URL (a UnitMCP client-server application)
    # Note: Replace with an actual UnitMCP repository URL
    git_url = "https://github.com/example/unitmcp-example.git"
    
    # Create a temporary directory for the repository
    import tempfile
    target_dir = tempfile.mkdtemp()
    
    try:
        # Create and run the Git Runner Integration
        integration = GitRunnerIntegration(
            git_url=git_url,
            target_dir=target_dir,
            branch=None,           # Use default branch
            interactive=True,      # Enable interactive mode
            auto_start=True,       # Automatically start the application
            log_level="INFO",      # Set log level
            server_host="localhost",  # Server host
            server_port=8888,         # Server port
            mode="both",              # Run both server and client
            simulation=True           # Run in simulation mode
        )
        
        # Run the Git Runner Integration
        exit_code = await integration.run()
        
        print(f"Git Runner Integration exited with code: {exit_code}")
        print(f"Repository cloned to: {target_dir}")
        
        # Keep the application running for a while
        print("Application is running. Press Ctrl+C to stop...")
        try:
            await asyncio.sleep(60)  # Run for 60 seconds
        except asyncio.CancelledError:
            pass
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(target_dir)


async def main():
    """Main function."""
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="UnitMCP Git Runner Example")
    parser.add_argument("--example", choices=["simple", "unitmcp"], default="simple",
                       help="Example to run: simple or unitmcp (default: simple)")
    args = parser.parse_args()
    
    # Run the selected example
    if args.example == "simple":
        await run_simple_example()
    elif args.example == "unitmcp":
        await run_unitmcp_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample stopped by user")
    except Exception as e:
        print(f"Error running example: {e}")
