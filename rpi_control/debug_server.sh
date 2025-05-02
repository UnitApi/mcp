#!/bin/bash

# Simple script to debug the hardware server on the remote host
# This will start the server in the foreground and show all output

# Source environment variables
if [[ -f .env ]]; then
    source .env
    echo "Loaded configuration from .env file"
fi

# Default values
REMOTE_HOST=${RPI_HOST:-"localhost"}
REMOTE_USER=${RPI_USERNAME:-"pi"}
REMOTE_DIR=${RPI_DIR:-"/tmp/hardware_server"}
PORT=${RPI_PORT:-8081}
HOST="0.0.0.0"

# Create remote directory
echo "Creating remote directory: $REMOTE_DIR"
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Copy necessary files
echo "Copying server script to remote host"
scp "examples/hardware_server.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo "Copying client script to remote host"
scp "examples/hardware_client.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Kill any existing process on the port
echo "Ensuring port $PORT is free on remote host"
ssh "$REMOTE_USER@$REMOTE_HOST" "fuser -k $PORT/tcp 2>/dev/null || true"
sleep 2

# Start the server in foreground mode to see all output
echo "Starting server on remote host at $HOST:$PORT in foreground mode"
echo "Press Ctrl+C to stop the server when done"
ssh -t "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_server.py --host '$HOST' --port '$PORT'"
