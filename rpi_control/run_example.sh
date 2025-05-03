#!/bin/bash
# run_example.sh: Run a specific example script with environment variable support
set -e

# Load .env if present
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
  echo "Loaded environment variables from .env file"
elif [ -f .env.development ]; then
  set -a
  . ./.env.development
  set +a
  echo "Loaded environment variables from .env.development file"
else
  echo "Warning: No .env or .env.development file found. Using default values."
fi

# Set default values if not provided in .env
: ${EXAMPLES_DIR:="$(dirname "$0")/examples"}
: ${RPI_HOST:="127.0.0.1"}
: ${RPI_PORT:="8080"}

if [ -z "$1" ]; then
    echo "Usage: $0 <example_script> [additional arguments]"
    echo "Available examples:"
    ls "$EXAMPLES_DIR" | grep -E '\.py$|\.sh$'
    echo ""
    echo "Environment variables:"
    echo "  EXAMPLES_DIR: $EXAMPLES_DIR"
    echo "  RPI_HOST: $RPI_HOST"
    echo "  RPI_PORT: $RPI_PORT"
    exit 1
fi

example="$1"

if [ ! -f "$EXAMPLES_DIR/$example" ]; then
    echo "Example '$example' not found in $EXAMPLES_DIR"
    exit 2
fi

# Prepare common arguments for Python scripts
COMMON_ARGS=""
if [[ "$example" == *.py ]]; then
    # Only add host/port for Python scripts
    COMMON_ARGS="--host $RPI_HOST --port $RPI_PORT"
fi

if [[ "$example" == *.py ]]; then
    shift
    echo -e "\n==============================="
    echo "Running $example with environment variables"
    echo "Host: $RPI_HOST, Port: $RPI_PORT"
    echo "Additional args: $@"
    echo "===============================\n"
    python3 "$EXAMPLES_DIR/$example" $COMMON_ARGS "$@"
    echo -e "\n===============================\n"
elif [[ "$example" == *.sh ]]; then
    shift
    echo -e "\n==============================="
    echo "Running $example with environment variables"
    echo "Host: $RPI_HOST, Port: $RPI_PORT"
    echo "Additional args: $@"
    echo "===============================\n"
    # Export variables for the shell script
    export RPI_HOST
    export RPI_PORT
    export EXAMPLES_DIR
    bash "$EXAMPLES_DIR/$example" "$@"
    echo -e "\n===============================\n"
else
    echo "Unknown file type: $example"
    exit 3
fi
