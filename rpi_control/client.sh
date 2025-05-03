#!/bin/bash
# client.sh: Run a client example
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
: ${SCRIPT_DIR:=$(dirname "$0")}
: ${EXAMPLE:="full_demo.py"}
: ${RPI_HOST:="127.0.0.1"}
: ${RPI_PORT:="8080"}

dir="${SCRIPT_DIR}"
cd "$dir"

echo "Running example: $EXAMPLE with host: $RPI_HOST and port: $RPI_PORT"

# Run the specified example with environment variables
if [ -f "examples/$EXAMPLE" ]; then
  python3 "examples/$EXAMPLE" --host "$RPI_HOST" --port "$RPI_PORT" "$@"
else
  echo "Error: Example file 'examples/$EXAMPLE' not found."
  echo "Available examples:"
  ls -1 examples/*.py
  exit 1
fi
