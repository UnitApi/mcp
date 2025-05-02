#!/bin/bash
# Check if port 8888 is already in use
if lsof -i :8888 | grep LISTEN; then
  echo "Port 8888 is already in use. Skipping server startup."
  SERVER_PID=""
else
  # Start the MCP hardware server in the background
  python ../../src/unitmcp/server/server_main.py &
  SERVER_PID=$!
  # Wait a few seconds for the server to start (adjust if needed)
  sleep 2
fi

# Run the port example client
python port.py

# Kill the server after the client finishes (if we started it)
if [ ! -z "$SERVER_PID" ]; then
  kill $SERVER_PID
fi
