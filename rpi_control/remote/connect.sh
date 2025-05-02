#!/bin/bash
# connect.sh - Securely copy your SSH public key to the remote host using .env data and diagnose connection

set -e

# Load .env from parent directory
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

if [ -z "$RPI_USERNAME" ] || [ -z "$RPI_HOST" ]; then
    echo "RPI_USERNAME or RPI_HOST not set in .env"
    exit 1
fi

# Use default key or allow override via env
KEY_FILE="${SSH_KEY:-$HOME/.ssh/id_ed25519.pub}"

if [ ! -f "$KEY_FILE" ]; then
    echo "SSH key file $KEY_FILE not found. Please generate one with ssh-keygen."
    exit 1
fi

# Use IdentitiesOnly to avoid 'Too many authentication failures'
echo "[connect.sh] Copying SSH public key to $RPI_USERNAME@$RPI_HOST ..."
ssh-copy-id -i "$KEY_FILE" -o IdentitiesOnly=yes "$RPI_USERNAME@$RPI_HOST"

# Diagnose connection
set +e
echo "[connect.sh] Testing passwordless SSH connection ..."
ssh -o BatchMode=yes -o ConnectTimeout=5 "$RPI_USERNAME@$RPI_HOST" "echo '[connect.sh] SSH connection successful.'"
if [ $? -ne 0 ]; then
    echo "[connect.sh] ERROR: SSH connection failed. Please check your SSH key, .env, and remote SSH configuration."
    exit 2
fi
set -e
echo "[connect.sh] SSH key installed and connection verified."
