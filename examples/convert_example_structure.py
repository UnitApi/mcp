#!/usr/bin/env python3
"""
UnitMCP Example Structure Converter

This script converts existing examples to follow the standardized structure with
runner.py, client.py, server.py, and config/ directory.
"""

import os
import sys
import shutil
import argparse
import logging
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


def convert_example(example_dir, template_dir, force=False):
    """
    Convert an example to follow the standardized structure.
    
    Parameters
    ----------
    example_dir : str
        Path to the example directory
    template_dir : str
        Path to the template directory
    force : bool
        Whether to overwrite existing files
        
    Returns
    -------
    bool
        True if the conversion was successful, False otherwise
    """
    try:
        example_name = os.path.basename(example_dir)
        logger.info(f"Converting example: {example_name}")
        
        # Create config directory if it doesn't exist
        config_dir = os.path.join(example_dir, "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            logger.info(f"Created config directory: {config_dir}")
        
        # Copy template files
        files_to_copy = {
            "runner.py": "runner.py",
            "client.py": "client.py",
            "server.py": "server.py",
            "config/client.yaml": "config/client.yaml",
            "config/server.yaml": "config/server.yaml",
        }
        
        for src_file, dst_file in files_to_copy.items():
            src_path = os.path.join(template_dir, src_file)
            dst_path = os.path.join(example_dir, dst_file)
            
            # Skip if file exists and force is False
            if os.path.exists(dst_path) and not force:
                logger.warning(f"File already exists, skipping: {dst_path}")
                continue
            
            # Copy the file
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied {src_file} to {dst_path}")
        
        # Create README.md if it doesn't exist
        readme_path = os.path.join(example_dir, "README.md")
        if not os.path.exists(readme_path) or force:
            # Get template README
            with open(os.path.join(template_dir, "README.md"), "r") as f:
                readme_template = f.read()
            
            # Replace template name with example name
            readme_content = readme_template.replace("UnitMCP Example Template", f"UnitMCP {example_name.replace('_', ' ').title()} Example")
            
            # Write README
            with open(readme_path, "w") as f:
                f.write(readme_content)
            
            logger.info(f"Created README.md: {readme_path}")
        
        # Create tests directory if it doesn't exist
        tests_dir = os.path.join(example_dir, "tests")
        if not os.path.exists(tests_dir):
            os.makedirs(tests_dir)
            logger.info(f"Created tests directory: {tests_dir}")
            
            # Copy test file
            test_file = os.path.join(template_dir, "tests/test_example.py")
            if os.path.exists(test_file):
                dst_test_file = os.path.join(tests_dir, f"test_{example_name}.py")
                shutil.copy2(test_file, dst_test_file)
                logger.info(f"Copied test file to {dst_test_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error converting example {example_name}: {e}")
        return False


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


def main():
    """
    Main function to convert examples.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="UnitMCP Example Structure Converter")
    
    parser.add_argument(
        "--examples-dir",
        type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to the examples directory",
    )
    
    parser.add_argument(
        "--template-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "template"),
        help="Path to the template directory",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    
    parser.add_argument(
        "--example",
        type=str,
        help="Convert only the specified example",
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert all examples",
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check examples without converting",
    )
    
    args = parser.parse_args()
    
    # Check if template directory exists
    if not os.path.exists(args.template_dir):
        print(f"{Fore.RED}Template directory not found: {args.template_dir}{Style.RESET_ALL}")
        return 1
    
    # Find examples to convert
    if args.example:
        # Convert only the specified example
        example_dir = os.path.join(args.examples_dir, args.example)
        if not os.path.exists(example_dir):
            print(f"{Fore.RED}Example not found: {example_dir}{Style.RESET_ALL}")
            return 1
        
        examples = [example_dir]
    elif args.all:
        # Convert all examples
        examples = find_examples(args.examples_dir)
    else:
        # Find non-compliant examples
        examples = []
        for example_dir in find_examples(args.examples_dir):
            components = check_example_structure(example_dir)
            if not all(components.values()):
                examples.append(example_dir)
    
    if not examples:
        print(f"{Fore.GREEN}No examples to convert{Style.RESET_ALL}")
        return 0
    
    print(f"{Fore.GREEN}Found {len(examples)} examples to convert{Style.RESET_ALL}")
    
    # Check or convert each example
    if args.check:
        # Just check examples
        for example_dir in examples:
            example_name = os.path.relpath(example_dir, args.examples_dir)
            components = check_example_structure(example_dir)
            missing_components = [c for c, present in components.items() if not present]
            if missing_components:
                print(f"{Fore.RED}✗ {example_name} - Missing: {', '.join(missing_components)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ {example_name} - Compliant{Style.RESET_ALL}")
    else:
        # Convert examples
        success_count = 0
        failure_count = 0
        
        for example_dir in examples:
            example_name = os.path.relpath(example_dir, args.examples_dir)
            print(f"Converting {example_name}...")
            
            if convert_example(example_dir, args.template_dir, args.force):
                success_count += 1
                print(f"{Fore.GREEN}✓ {example_name} - Converted successfully{Style.RESET_ALL}")
            else:
                failure_count += 1
                print(f"{Fore.RED}✗ {example_name} - Conversion failed{Style.RESET_ALL}")
        
        # Print summary
        print("\nSummary:")
        print(f"{Fore.GREEN}Successfully converted: {success_count}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed to convert: {failure_count}{Style.RESET_ALL}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
