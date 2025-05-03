#!/usr/bin/env python3
"""
Test runner for UnitMCP DSL and Claude 3.7 integration tests.

This script discovers and runs all tests for the UnitMCP DSL and Claude 3.7 integration.
"""

import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == '__main__':
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    
    # Only run tests in the dsl, llm, and cli directories
    test_dirs = [
        os.path.join(os.path.dirname(__file__), 'dsl'),
        os.path.join(os.path.dirname(__file__), 'llm'),
        os.path.join(os.path.dirname(__file__), 'cli')
    ]
    
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add tests from each directory
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            suite = test_loader.discover(start_dir=test_dir, pattern='test_*.py')
            test_suite.addTest(suite)
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())
