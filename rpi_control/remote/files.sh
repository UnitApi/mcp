#!/bin/bash
# update_remote.sh: Sync all files in rpi_control to a remote Raspberry Pi using .env only
set -e

# Load variables from .env
if [ -f .env ]; then
  set -a
  . .env
  set +a
  echo "Loaded variables from .env:"
  echo "RPI_USERNAME: $RPI_USERNAME"
  echo "REMOTE: $REMOTE"
  echo "REMOTE_PATH: $REMOTE_PATH"
else
  echo ".env file not found!"
  exit 1
fi

if [ -z "$RPI_USERNAME" ]; then
  echo "RPI_USERNAME is not set in .env! Exiting."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure remote path exists
ssh "$REMOTE" "mkdir -p $REMOTE_PATH"

# Sync all files in remote except venv, .git, __pycache__
rsync -avz --delete --exclude 'venv' --exclude '.git' --exclude '__pycache__' "$SCRIPT_DIR/" "$REMOTE:$REMOTE_PATH/"
#rsync -avz --exclude 'venv' --exclude '.git' --exclude '__pycache__' "$SCRIPT_DIR/" "$REMOTE:$REMOTE_PATH/"

echo "[update_remote.sh] Files synced to $REMOTE:$REMOTE_PATH"
