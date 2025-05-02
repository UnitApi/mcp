#!/bin/bash
# start.sh: Run install.sh and start all example clients in examples/
set -e

# Load .env if present
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

dir="${SCRIPT_DIR:-$(dirname "$0")}"
cd "$dir"

bash install.sh

echo "[rpi_control] Running all examples in examples/ ..."

for example in examples/*.py; do
    echo "[rpi_control] Running $example ..."
    python3 "$example"
done
