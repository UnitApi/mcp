#!/usr/bin/env python3
"""
Custom Orchestrator Shell Example

This example demonstrates how to create a custom orchestrator shell
with additional commands for specific use cases.
"""

import os
import sys
import time
import logging
import argparse
from colorama import Fore, Style, init
from unitmcp.orchestrator import Orchestrator, OrchestratorShell

# Initialize colorama
init()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class CustomOrchestratorShell(OrchestratorShell):
    """
    Custom orchestrator shell with additional commands.
    
    This shell extends the standard OrchestratorShell with additional
    commands for specific use cases.
    """
    
    def __init__(self, orchestrator, custom_config=None):
        """Initialize the custom shell."""
        super().__init__(orchestrator)
        self.custom_config = custom_config or {}
        
        # Update the intro banner
        self.intro = f"""
{Fore.GREEN}╔══════════════════════════════════════════╗
║  {Fore.YELLOW}Custom UnitMCP Orchestrator{Fore.GREEN}          ║
║  {Fore.CYAN}Type 'help' for commands | 'exit' to quit{Fore.GREEN}  ║
╚══════════════════════════════════════════╝{Style.RESET_ALL}
"""
    
    def do_monitor(self, arg):
        """
        Monitor a running example and display real-time status.
        
        Usage: monitor [runner_id]
        If no runner_id is specified, monitors the most recently started runner.
        """
        args = arg.split()
        runner_id = args[0] if args else None
        
        # If no runner_id specified, use the most recent one
        if not runner_id:
            active_runners = self.orchestrator.get_active_runners()
            if not active_runners:
                print(f"{Fore.YELLOW}No active runners to monitor.{Style.RESET_ALL}")
                return
            
            # Get the most recent runner
            runner_id = list(active_runners.keys())[0]
        
        # Check if the runner exists
        if runner_id not in self.orchestrator.get_active_runners():
            print(f"{Fore.RED}Runner '{runner_id}' not found.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}Monitoring runner: {runner_id}{Style.RESET_ALL}")
        print(f"Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Get runner status
                status = self.orchestrator.get_runner_status(runner_id)
                
                # Clear the screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Print status
                print(f"{Fore.GREEN}Runner: {runner_id}{Style.RESET_ALL}")
                print(f"Status: {status.get('status', 'unknown')}")
                print(f"Example: {status.get('example', 'unknown')}")
                print(f"Host: {status.get('host', 'unknown')}")
                print(f"Port: {status.get('port', 'unknown')}")
                print(f"Simulation: {'Yes' if status.get('simulation') else 'No'}")
                print(f"Started: {status.get('start_time', 'unknown')}")
                print(f"Uptime: {status.get('uptime', 'unknown')} seconds")
                
                # Wait before refreshing
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\nStopped monitoring")
    
    def do_batch(self, arg):
        """
        Run a batch of examples in sequence.
        
        Usage: batch example1 example2 example3 ...
        """
        examples = arg.split()
        
        if not examples:
            print(f"{Fore.YELLOW}No examples specified.{Style.RESET_ALL}")
            print(f"Usage: batch example1 example2 example3 ...")
            return
        
        print(f"{Fore.GREEN}Running batch of {len(examples)} examples:{Style.RESET_ALL}")
        
        for i, example_name in enumerate(examples):
            print(f"\n{Fore.CYAN}[{i+1}/{len(examples)}] Running example: {example_name}{Style.RESET_ALL}")
            
            # Check if the example exists
            if example_name not in self.orchestrator.get_examples():
                print(f"{Fore.RED}Example '{example_name}' not found. Skipping.{Style.RESET_ALL}")
                continue
            
            # Run the example
            runner_info = self.orchestrator.run_example(example_name, simulation=True)
            
            if runner_info["status"] == "running":
                print(f"Runner started with ID: {runner_info['id']}")
                
                # Wait for 5 seconds
                print("Waiting for 5 seconds...")
                time.sleep(5)
                
                # Stop the runner
                self.orchestrator.stop_runner(runner_info["id"])
                print(f"Runner stopped")
            else:
                print(f"{Fore.RED}Failed to start runner: {runner_info.get('error', 'Unknown error')}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}Batch completed.{Style.RESET_ALL}")
    
    def do_export(self, arg):
        """
        Export the configuration of an example to a file.
        
        Usage: export <example_name> <filename>
        """
        args = arg.split()
        
        if len(args) != 2:
            print(f"{Fore.YELLOW}Invalid arguments.{Style.RESET_ALL}")
            print(f"Usage: export <example_name> <filename>")
            return
        
        example_name, filename = args
        
        # Check if the example exists
        if example_name not in self.orchestrator.get_examples():
            print(f"{Fore.RED}Example '{example_name}' not found.{Style.RESET_ALL}")
            return
        
        # Get example info
        example_info = self.orchestrator.get_example(example_name)
        
        # Export to file
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(example_info, f, indent=2)
            
            print(f"{Fore.GREEN}Example configuration exported to: {filename}{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"{Fore.RED}Failed to export configuration: {e}{Style.RESET_ALL}")

def main():
    """Main entry point for the custom shell example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Custom Orchestrator Shell Example")
    parser.add_argument("--examples-dir", help="Path to examples directory")
    parser.add_argument("--config-file", help="Path to configuration file")
    parser.add_argument("--log-level", default="WARNING", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Set the logging level")
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose output")
    args = parser.parse_args()
    
    # Set log level
    log_level = "INFO" if args.verbose else args.log_level
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Create an Orchestrator instance
    orchestrator = Orchestrator(
        examples_dir=args.examples_dir,
        config_file=args.config_file,
        quiet=not args.verbose
    )
    
    # Custom configuration
    custom_config = {
        "batch_timeout": 5,  # Seconds to wait between batch examples
        "monitor_refresh": 2  # Seconds between monitor updates
    }
    
    # Create and run the custom shell
    shell = CustomOrchestratorShell(orchestrator, custom_config)
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error in shell: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
