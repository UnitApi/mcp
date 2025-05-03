#!/usr/bin/env python3
"""
Run the Enhanced Orchestrator Shell

This script sets up the Python path and runs the enhanced orchestrator shell.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import and run the enhanced shell
from examples.audio.enhanced_shell import main

if __name__ == "__main__":
    main()
