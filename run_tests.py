#!/usr/bin/env python3
"""
Test runner for UnitMCP tests.

This script discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os
import argparse
import logging

def setup_logging(verbose=False):
    """
    Set up logging configuration.
    
    Args:
        verbose (bool): Whether to enable verbose logging.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_tests(pattern=None, verbose=False):
    """
    Run the tests.
    
    Args:
        pattern (str): Pattern to match test files.
        verbose (bool): Whether to enable verbose output.
    
    Returns:
        bool: True if all tests passed, False otherwise.
    """
    # Add the src directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
    
    # Set up the test loader
    loader = unittest.TestLoader()
    
    # Discover tests
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    if pattern:
        pattern = f'test_{pattern}.py'
    else:
        pattern = 'test_*.py'
    
    suite = loader.discover(start_dir, pattern=pattern)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description='Run UnitMCP tests')
    parser.add_argument('-p', '--pattern', help='Pattern to match test files (without "test_" prefix and ".py" suffix)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    success = run_tests(args.pattern, args.verbose)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
