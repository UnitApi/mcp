#!/usr/bin/env python3

try:
    from unitmcp.core import LoggingManager, ConfigManager
    print("Successfully imported LoggingManager and ConfigManager")
except ImportError as e:
    print(f"Import failed: {e}")
    import sys
    print("\nPython path:")
    for path in sys.path:
        print(path)
