#!/bin/bash
# start_service.sh - Run a Python example from examples/ as a background service reachable from your machine

set -e

# Load .env from parent directory
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

if [ -z "$RPI_USERNAME" ] || [ -z "$RPI_HOST" ] || [ -z "$EXAMPLE" ] || [ -z "$EXAMPLES_DIR" ] || [ -z "$PORT" ] || [ -z "$LOGFILE" ]; then
    echo "RPI_USERNAME, RPI_HOST, EXAMPLE, EXAMPLES_DIR, PORT, or LOGFILE not set in .env"
    exit 1
fi

REMOTE="$RPI_USERNAME@$RPI_HOST"

# Use a here-document to avoid quoting issues
ssh "$REMOTE" bash <<EOF
cd "$EXAMPLES_DIR"
fuser -k ${PORT}/tcp 2>/dev/null || true
nohup python3 "$EXAMPLE" > "$LOGFILE" 2>&1 &
echo "Started $EXAMPLE from $EXAMPLES_DIR as a background service (log: $LOGFILE)"
EOF
