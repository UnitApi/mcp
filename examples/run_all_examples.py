#!/usr/bin/env python3
"""
UnitMCP Example Runner

This script runs all examples in the examples directory to verify they work correctly.
It can be used to test that all examples are properly configured and can be started.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import json
import yaml
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_examples(examples_dir):
    """
    Find all examples in the examples directory.
    
    Parameters
    ----------
    examples_dir : str
        Path to the examples directory
        
    Returns
    -------
    list
        List of example directories
    """
    examples = []
    
    # Walk through the examples directory
    for root, dirs, files in os.walk(examples_dir):
        # Skip the runner directory and template directory
        if "runner" in root.split(os.path.sep) or "template" in root.split(os.path.sep):
            continue
            
        # Skip test directories
        if "tests" in root.split(os.path.sep):
            continue
            
        # Check if this directory has a runner.py file
        if "runner.py" in files:
            examples.append(root)
    
    return examples


def run_example(example_dir, timeout=30, verbose=False, port_offset=0):
    """
    Run an example.
    
    Parameters
    ----------
    example_dir : str
        Path to the example directory
    timeout : int
        Timeout in seconds
    verbose : bool
        Whether to print verbose output
    port_offset : int
        Port offset to avoid conflicts
        
    Returns
    -------
    bool
        True if the example ran successfully, False otherwise
    """
    logger.info(f"Running example in {example_dir}")
    
    # Get the runner.py path
    runner_path = os.path.join(example_dir, "runner.py")
    
    if not os.path.exists(runner_path):
        logger.error(f"Runner not found: {runner_path}")
        return False
    
    # Get the example name
    example_name = os.path.basename(example_dir)
    
    # Update config files with unique ports if they exist
    server_config_path = os.path.join(example_dir, "config", "server.yaml")
    client_config_path = os.path.join(example_dir, "config", "client.yaml")
    
    # Use a unique port for each example
    server_port = 9000 + port_offset
    
    if os.path.exists(server_config_path):
        try:
            # Load the server config
            with open(server_config_path, "r") as f:
                server_config = yaml.safe_load(f) or {}
            
            # Update the port
            if "server" not in server_config:
                server_config["server"] = {}
            server_config["server"]["port"] = server_port
            
            # Save the updated config
            with open(server_config_path, "w") as f:
                yaml.dump(server_config, f)
            
            logger.info(f"Updated server port to {server_port} in {server_config_path}")
        except Exception as e:
            logger.warning(f"Error updating server config: {e}")
    
    if os.path.exists(client_config_path):
        try:
            # Load the client config
            with open(client_config_path, "r") as f:
                client_config = yaml.safe_load(f) or {}
            
            # Update the port
            if "connection" not in client_config:
                client_config["connection"] = {}
            client_config["connection"]["server_port"] = server_port
            
            # Save the updated config
            with open(client_config_path, "w") as f:
                yaml.dump(client_config, f)
            
            logger.info(f"Updated client port to {server_port} in {client_config_path}")
        except Exception as e:
            logger.warning(f"Error updating client config: {e}")
    
    # Create a temporary file to provide input to the example
    input_file = os.path.join(example_dir, ".test_input.txt")
    with open(input_file, "w") as f:
        f.write("help\nexit\n")
    
    # Run the example
    try:
        logger.info(f"Starting example: {example_name}")
        
        # Build the command
        cmd = [sys.executable, runner_path]
        
        # Run the example with a timeout and provide input
        with open(input_file, "r") as input_stream:
            process = subprocess.Popen(
                cmd,
                stdin=input_stream,
                stdout=subprocess.PIPE if not verbose else None,
                stderr=subprocess.PIPE if not verbose else None,
                text=True,
                cwd=example_dir,
            )
            
            # Wait for a short time to let the example start
            time.sleep(5)
            
            # Check if the process is still running
            if process.poll() is None:
                logger.info(f"Example {example_name} started successfully")
                
                # Wait a bit longer to let the commands execute
                time.sleep(2)
                
                # Kill the process
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Example {example_name} did not terminate, killing...")
                    process.kill()
                
                # Clean up the input file
                if os.path.exists(input_file):
                    os.remove(input_file)
                
                # If we got this far, consider it a success
                logger.info(f"Example {example_name} ran successfully")
                return True
            else:
                # Process exited early
                returncode = process.returncode
                stdout, stderr = process.communicate()
                
                # Check if the process exited normally (could be due to the exit command)
                if returncode == 0:
                    logger.info(f"Example {example_name} exited normally")
                    
                    # Clean up the input file
                    if os.path.exists(input_file):
                        os.remove(input_file)
                    
                    return True
                else:
                    logger.error(f"Example {example_name} exited with code {returncode}")
                    if stdout and verbose:
                        logger.info(f"Stdout: {stdout}")
                    if stderr:
                        logger.error(f"Stderr: {stderr}")
                    
                    # Clean up the input file
                    if os.path.exists(input_file):
                        os.remove(input_file)
                    
                    return False
        
    except Exception as e:
        logger.error(f"Error running example {example_name}: {e}")
        
        # Clean up the input file
        if os.path.exists(input_file):
            os.remove(input_file)
        
        return False


def generate_report(results, output_file=None):
    """
    Generate a report of the test results.
    
    Parameters
    ----------
    results : dict
        Dictionary of test results
    output_file : str, optional
        Path to the output file
        
    Returns
    -------
    str
        Report as a string
    """
    # Calculate statistics
    total = len(results)
    success = sum(1 for result in results.values() if result)
    failure = total - success
    
    # Generate report
    report = []
    report.append("# UnitMCP Example Test Report")
    report.append("")
    report.append(f"## Summary")
    report.append("")
    report.append(f"- Total examples: {total}")
    report.append(f"- Successful: {success}")
    report.append(f"- Failed: {failure}")
    report.append(f"- Success rate: {success / total * 100:.1f}%")
    report.append("")
    report.append("## Details")
    report.append("")
    
    # Sort results by status and name
    sorted_results = sorted(results.items(), key=lambda x: (not x[1], x[0]))
    
    for example, success in sorted_results:
        status = "✅ Success" if success else "❌ Failure"
        report.append(f"- **{example}**: {status}")
    
    # Join report lines
    report_str = "\n".join(report)
    
    # Write to file if specified
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_str)
    
    return report_str


def main():
    """
    Main function to run all examples.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Runner")
    
    parser.add_argument(
        "--examples-dir",
        type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to the examples directory",
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each example",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "--examples",
        type=str,
        nargs="+",
        help="Run specific examples (space-separated list)",
    )
    
    parser.add_argument(
        "--report",
        type=str,
        help="Generate a report and save it to the specified file",
    )
    
    parser.add_argument(
        "--json",
        type=str,
        help="Save results as JSON to the specified file",
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Find all examples
    if args.examples:
        # Run only the specified examples
        examples = []
        for example in args.examples:
            example_dir = os.path.join(args.examples_dir, example)
            if not os.path.exists(example_dir):
                logger.error(f"Example not found: {example_dir}")
                return 1
            examples.append(example_dir)
    else:
        # Run all examples
        examples = find_examples(args.examples_dir)
    
    if not examples:
        logger.error("No examples found")
        return 1
    
    logger.info(f"Found {len(examples)} examples")
    
    # Run each example
    results = {}
    port_offset = 0
    
    for example_dir in examples:
        example_name = os.path.relpath(example_dir, args.examples_dir)
        results[example_name] = run_example(example_dir, args.timeout, args.verbose, port_offset)
        port_offset += 1
    
    # Print summary
    success_count = sum(1 for result in results.values() if result)
    failure_count = len(results) - success_count
    
    print(f"\n{Fore.GREEN}Summary: {success_count} examples succeeded, {Fore.RED}{failure_count} examples failed{Style.RESET_ALL}")
    
    # Generate report if requested
    if args.report:
        report = generate_report(results, args.report)
        print(f"\nReport saved to {args.report}")
    
    # Save results as JSON if requested
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.json}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
