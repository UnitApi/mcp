#!/bin/bash
# scp.sh: Copy all files from rpi_control folder and its dependencies to a remote machine
# Usage: bash scp.sh [user@remote_host] [remote_path] [--no-replace]
# 
# By default, this script will replace (overwrite) existing files on the remote machine.
# Use the --no-replace option to skip files that already exist on the remote machine.
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

# Load .env from project root
if [ -f ../../.env ]; then
  set -a
  . ../../.env
  set +a
fi

# Parse command line arguments
NO_REPLACE=false
ARGS=()

for arg in "$@"; do
  if [ "$arg" = "--no-replace" ]; then
    NO_REPLACE=true
  else
    ARGS+=("$arg")
  fi
done

# Use command line arguments or environment variables
REMOTE="${ARGS[0]:-$REMOTE}"
REMOTE_PATH="${ARGS[1]:-$REMOTE_PATH}"

# Check if RPI_USERNAME and RPI_HOST are set in environment
if [ -z "$REMOTE" ] && [ -n "$RPI_USERNAME" ] && [ -n "$RPI_HOST" ]; then
    REMOTE="$RPI_USERNAME@$RPI_HOST"
    REMOTE_PATH="${REMOTE_PATH:-/home/$RPI_USERNAME}"
fi

if [ -z "$REMOTE" ]; then
    echo "Usage: $0 user@remote_host [remote_path]"
    echo "Or set RPI_USERNAME and RPI_HOST in .env file"
    exit 1
fi

# Ensure remote path is set
REMOTE_PATH="${REMOTE_PATH:-/home/${REMOTE%%@*}}"

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
echo $PROJECT_ROOT
#exit 0
echo "[scp.sh] Copying all files from rpi_control and dependencies to $REMOTE:$REMOTE_PATH ..."

# Create the remote directory
ssh "$REMOTE" "mkdir -p $REMOTE_PATH"

# Set rsync options based on NO_REPLACE flag
RSYNC_OPTS="-av"
if [ "$NO_REPLACE" = true ]; then
    RSYNC_OPTS="$RSYNC_OPTS --ignore-existing"
    echo "[scp.sh] Running in no-replace mode - existing files will not be overwritten"
fi

# First, copy the src directory (for unitmcp) and other dependencies
#echo "[scp.sh] Copying project dependencies..."
#rsync $RSYNC_OPTS --exclude 'venv' \
#                 --exclude '*.pyc' \
#                 --exclude '__pycache__' \
#                 --exclude '.git' \
#                 --exclude '.vscode' \
#                 --exclude '*.egg-info' \
#                 --exclude '.tox' \
#                 --exclude '.pytest_cache' \
#                 --exclude '.idea' \
#                 --exclude '*.wav' \
#                 --exclude '*.mp3' \
#                 "$PROJECT_ROOT/" "$REMOTE:$REMOTE_PATH/"
#
## Copy setup files needed for installation
#rsync $RSYNC_OPTS "$PROJECT_ROOT/setup.py" "$PROJECT_ROOT/setup.cfg" "$PROJECT_ROOT/pyproject.toml" "$PROJECT_ROOT/MANIFEST.in" "$REMOTE:$REMOTE_PATH/" 2>/dev/null || true

# Then, copy the entire rpi_control directory
#echo "[scp.sh] Copying rpi_control directory..."
rsync $RSYNC_OPTS --exclude 'venv' \
                 --exclude '*.pyc' \
                 --exclude '__pycache__' \
                 "$PROJECT_ROOT/" "$REMOTE:$REMOTE_PATH/"

echo "[scp.sh] File copy to $REMOTE complete."
echo "[scp.sh] To install on the remote machine, run: ssh $REMOTE \"cd $REMOTE_PATH/remote && bash install.sh\""
