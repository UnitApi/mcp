#!/usr/bin/env python3
"""
Test script to verify the env_loader.py fix for handling sets and tuples.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from unitmcp.utils.env_loader import EnvLoader

def test_resolve_env_vars_with_set():
    """Test that sets can be properly resolved in env_loader."""
    env_loader = EnvLoader()
    
    # Test with a set
    test_set = {"TEST1", "TEST2", "${HOME}"}
    resolved_set = env_loader.resolve_env_vars(test_set)
    
    print(f"Original set: {test_set}")
    print(f"Resolved set: {resolved_set}")
    
    # Verify that the set was properly resolved
    assert isinstance(resolved_set, set), "Result should still be a set"
    assert len(resolved_set) == 3, "Set should still have 3 items"
    
    # Test with a tuple
    test_tuple = ("TEST1", "TEST2", "${HOME}")
    resolved_tuple = env_loader.resolve_env_vars(test_tuple)
    
    print(f"Original tuple: {test_tuple}")
    print(f"Resolved tuple: {resolved_tuple}")
    
    # Verify that the tuple was properly resolved
    assert isinstance(resolved_tuple, tuple), "Result should still be a tuple"
    assert len(resolved_tuple) == 3, "Tuple should still have 3 items"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_resolve_env_vars_with_set()
