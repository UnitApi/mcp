#!/bin/bash
# start_service.sh - Start a simple example server for testing

# Example: Start a simple Python HTTP server on port 8081
PORT=8081
LOGFILE="example_server.log"

# Kill any process already using the port (optional, for clean restart)
fuser -k ${PORT}/tcp 2>/dev/null || true

# Start the server in the background
nohup python3 -m http.server $PORT > $LOGFILE 2>&1 &
echo "Started example Python HTTP server on port $PORT (log: $LOGFILE)"
