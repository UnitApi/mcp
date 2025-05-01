#!/bin/bash
# Wrapper script for ssh_connect.py
# This ensures that ssh_connect.py is executed with Python

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Execute the Python script with all arguments passed to this wrapper
python3 "$SCRIPT_DIR/ssh_connect.py" "$@"
