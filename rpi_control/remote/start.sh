#!/bin/bash
set -e

# Load .env from parent directory
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

# Load .env from parent directory
if [ -f ../.env ]; then
  set -a
  . ../.env
  set +a
fi

# Activate venv
if [ ! -d "venv" ]; then
  echo "[rpi_control] ERROR: venv not found. Run install.sh first."
  exit 1
fi
source venv/bin/activate

# Default: run all Python examples listed in $EXAMPLES, or all in examples if not set
if [ -z "$EXAMPLES" ]; then
  EXAMPLES=$(ls examples/*.py | xargs -n1 basename)
fi

echo "[rpi_control] Starting examples: $EXAMPLES"

for example in $EXAMPLES; do
  if [ -f "examples/$example" ]; then
    echo "--- Running $example ---"
    python "examples/$example"
  else
    echo "[WARN] Example not found: examples/$example"
  fi
done
