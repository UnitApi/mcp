#!/bin/bash
# install_remote.sh: Install rpi_control on a remote machine via SSH
# Usage: bash install_remote.sh [user@remote_host] [remote_path]
set -e

# Load .env if present
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

REMOTE="${1:-$REMOTE}"
REMOTE_PATH="${2:-$REMOTE_PATH}"

if [ -z "$REMOTE" ]; then
    echo "Usage: $0 user@remote_host [remote_path]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Copy all relevant files to remote
ssh "$REMOTE" "mkdir -p $REMOTE_PATH"
scp -r "$SCRIPT_DIR"/* "$REMOTE":"$REMOTE_PATH"/

# Run install.sh on remote
ssh "$REMOTE" "cd $REMOTE_PATH && bash install.sh"

echo "[install_remote.sh] Installation on $REMOTE complete."
