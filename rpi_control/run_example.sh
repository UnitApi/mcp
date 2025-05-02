#!/bin/bash
set -e

EXAMPLES_DIR="$(dirname "$0")/examples"

if [ -z "$1" ]; then
    echo "Usage: $0 <example_script>"
    echo "Available examples:"
    ls "$EXAMPLES_DIR" | grep -E '\.py$|\.sh$'
    exit 1
fi

example="$1"

if [ ! -f "$EXAMPLES_DIR/$example" ]; then
    echo "Example '$example' not found in $EXAMPLES_DIR"
    exit 2
fi

if [[ "$example" == *.py ]]; then
    shift
    echo "\n==============================="
    echo "Running $example $@"
    echo "===============================\n"
    python3 "$EXAMPLES_DIR/$example" "$@"
    echo "\n===============================\n"
elif [[ "$example" == *.sh ]]; then
    shift
    echo "\n==============================="
    echo "Running $example $@"
    echo "===============================\n"
    bash "$EXAMPLES_DIR/$example" "$@"
    echo "\n===============================\n"
else
    echo "Unknown file type: $example"
    exit 3
fi
