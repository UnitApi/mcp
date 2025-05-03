#!/bin/bash
# start.sh: Run install.sh and start all example clients in examples/
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
: ${RPI_HOST:="127.0.0.1"}
: ${RPI_PORT:="8080"}
: ${EXAMPLES_DIR:="examples"}

dir="${SCRIPT_DIR}"
cd "$dir"

# Run the installation script if needed
if [ "$SKIP_INSTALL" != "true" ]; then
  bash install.sh
fi

echo "[rpi_control] Running all examples in ${EXAMPLES_DIR}/ with host: $RPI_HOST and port: $RPI_PORT ..."

# Check if specific examples are specified
if [ -n "$SPECIFIC_EXAMPLES" ]; then
  IFS=',' read -ra EXAMPLE_LIST <<< "$SPECIFIC_EXAMPLES"
  for example in "${EXAMPLE_LIST[@]}"; do
    example_path="${EXAMPLES_DIR}/${example}"
    if [ -f "$example_path" ]; then
      echo "[rpi_control] Running $example_path ..."
      python3 "$example_path" --host "$RPI_HOST" --port "$RPI_PORT"
    else
      echo "[rpi_control] Warning: Example $example_path not found, skipping."
    fi
  done
else
  # Run all examples
  for example in ${EXAMPLES_DIR}/*.py; do
    echo "[rpi_control] Running $example ..."
    python3 "$example" --host "$RPI_HOST" --port "$RPI_PORT"
  done
fi
