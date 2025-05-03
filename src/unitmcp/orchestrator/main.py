"""Main entry point for the UnitMCP Orchestrator."""

import os
import sys
import argparse
import logging
from .shell import OrchestratorShell
from .orchestrator import Orchestrator

def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(description="UnitMCP Orchestrator")
    parser.add_argument("--examples-dir", help="Path to examples directory")
    parser.add_argument("--config-file", help="Path to configuration file")
    parser.add_argument("--log-level", default="WARNING", 
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Set the logging level")
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose output (sets log level to INFO)")
    parser.add_argument("--no-shell", action="store_true", 
                      help="Don't start interactive shell")
    parser.add_argument("--run", help="Run an example")
    parser.add_argument("--simulation", type=lambda x: x.lower() == "true", 
                      help="Run in simulation mode")
    parser.add_argument("--host", help="Host to connect to")
    parser.add_argument("--port", type=int, help="Port to use")
    parser.add_argument("--ssh-username", help="SSH username")
    parser.add_argument("--ssh-key-path", help="Path to SSH key")
    parser.add_argument("--ssl", type=lambda x: x.lower() == "true", 
                      help="Enable SSL")
    
    args = parser.parse_args()
    
    # Set log level to INFO if verbose flag is set
    if args.verbose:
        log_level = "INFO"
    else:
        log_level = args.log_level
    
    # Configure logging with minimal format for non-debug levels
    if log_level == "DEBUG":
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(levelname)s: %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format
    )
    
    # Create orchestrator with minimal output
    orchestrator = Orchestrator(
        examples_dir=args.examples_dir,
        config_file=args.config_file,
        quiet=not args.verbose
    )
    
    # Run example if specified
    if args.run:
        example_name = args.run
        
        if example_name not in orchestrator.get_examples():
            print(f"Error: Example '{example_name}' not found")
            sys.exit(1)
        
        # Prepare options
        options = {}
        if args.simulation is not None:
            options["simulation"] = args.simulation
        if args.host:
            options["host"] = args.host
        if args.port:
            options["port"] = args.port
        if args.ssh_username:
            options["ssh_username"] = args.ssh_username
        if args.ssh_key_path:
            options["ssh_key_path"] = args.ssh_key_path
        if args.ssl is not None:
            options["ssl_enabled"] = args.ssl
        
        # Run example
        print(f"Running example: {example_name}")
        runner_info = orchestrator.run_example(example_name, **options)
        
        if runner_info["status"] == "running":
            print(f"Runner started with ID: {runner_info['id']}")
            
            # If not starting shell, wait for runner to finish
            if args.no_shell:
                process = runner_info.get("process")
                if process:
                    print("Waiting for runner to finish...")
                    process.wait()
                    
                    # Get output
                    stdout = process.stdout.read() if process.stdout else b""
                    stderr = process.stderr.read() if process.stderr else b""
                    
                    if stdout:
                        print("\nOutput:")
                        print(stdout.decode())
                    
                    if stderr:
                        print("\nErrors:")
                        print(stderr.decode())
                    
                    print(f"Runner finished with return code: {process.returncode}")
                    sys.exit(process.returncode)
        else:
            print(f"Failed to start runner: {runner_info.get('error', 'Unknown error')}")
            sys.exit(1)
    
    # Start shell if not disabled
    if not args.no_shell:
        shell = OrchestratorShell(orchestrator)
        
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            logging.error(f"Error in shell: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
