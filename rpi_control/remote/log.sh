#!/bin/bash
# show_log.sh - Show the latest log output from the example service running on the remote machine

set -e

# Load .env from parent directory
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

if [ -z "$RPI_USERNAME" ] || [ -z "$RPI_HOST" ] || [ -z "$LOGFILE" ] || [ -z "$EXAMPLES_DIR" ]; then
    echo "RPI_USERNAME, RPI_HOST, LOGFILE, or EXAMPLES_DIR not set in .env"
    exit 1
fi

REMOTE="$RPI_USERNAME@$RPI_HOST"

ssh "$REMOTE" "tail -n 50 $EXAMPLES_DIR/$LOGFILE"
