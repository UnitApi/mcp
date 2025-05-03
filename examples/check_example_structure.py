#!/usr/bin/env python3
"""
UnitMCP Example Structure Checker

This script checks all examples in the examples directory to verify they follow
the standardized structure with runner.py, client.py, server.py, and config/ directory.
"""

import os
import sys
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init()


def check_example_structure(example_dir):
    """
    Check if an example follows the standardized structure.
    
    Parameters
    ----------
    example_dir : str
        Path to the example directory
        
    Returns
    -------
    dict
        Dictionary with the status of each required component
    """
    # Required components
    required_components = {
        'runner.py': False,
        'client.py': False,
        'server.py': False,
        'config/': False,
        'README.md': False
    }
    
    # Check if each component exists
    for component in required_components:
        if component.endswith('/'):
            # It's a directory
            component_path = os.path.join(example_dir, component.rstrip('/'))
            required_components[component] = os.path.isdir(component_path)
        else:
            # It's a file
            component_path = os.path.join(example_dir, component)
            required_components[component] = os.path.isfile(component_path)
    
    return required_components


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
            
        # Skip directories that are not examples
        if not any(f.endswith('.py') for f in files):
            continue
            
        # Skip root directory
        if root == examples_dir:
            continue
            
        # Add to examples list
        examples.append(root)
    
    return examples


def main():
    """
    Main function to check all examples.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Structure Checker")
    
    parser.add_argument(
        "--examples-dir",
        type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to the examples directory",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show details for all examples, not just those that need updates",
    )
    
    parser.add_argument(
        "--example",
        type=str,
        help="Check only the specified example",
    )
    
    args = parser.parse_args()
    
    # Find examples to check
    if args.example:
        # Check only the specified example
        example_dir = os.path.join(args.examples_dir, args.example)
        if not os.path.exists(example_dir):
            print(f"{Fore.RED}Example not found: {example_dir}{Style.RESET_ALL}")
            return 1
        
        examples = [example_dir]
    else:
        # Check all examples
        examples = find_examples(args.examples_dir)
    
    if not examples:
        print(f"{Fore.RED}No examples found{Style.RESET_ALL}")
        return 1
    
    print(f"{Fore.GREEN}Found {len(examples)} examples{Style.RESET_ALL}")
    
    # Check each example
    compliant_examples = []
    non_compliant_examples = []
    
    for example_dir in examples:
        # Get the example name (relative to examples directory)
        example_name = os.path.relpath(example_dir, args.examples_dir)
        
        # Check the example structure
        components = check_example_structure(example_dir)
        
        # Check if all components are present
        is_compliant = all(components.values())
        
        if is_compliant:
            compliant_examples.append(example_name)
            if args.verbose:
                print(f"{Fore.GREEN}✓ {example_name} - Compliant{Style.RESET_ALL}")
        else:
            non_compliant_examples.append((example_name, components))
            missing_components = [c for c, present in components.items() if not present]
            print(f"{Fore.RED}✗ {example_name} - Missing: {', '.join(missing_components)}{Style.RESET_ALL}")
    
    # Print summary
    print("\nSummary:")
    print(f"{Fore.GREEN}Compliant examples: {len(compliant_examples)}{Style.RESET_ALL}")
    print(f"{Fore.RED}Non-compliant examples: {len(non_compliant_examples)}{Style.RESET_ALL}")
    
    if non_compliant_examples:
        print("\nExamples that need to be updated:")
        for example_name, components in non_compliant_examples:
            missing_components = [c for c, present in components.items() if not present]
            print(f"- {example_name} (Missing: {', '.join(missing_components)})")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
