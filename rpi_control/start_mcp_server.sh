#!/bin/bash
clear
set -e
EXAMPLES_DIR="$(dirname "$0")/examples"
SERVER_SCRIPT="llm_hardware_control.py"

# --- Argument splitting: server args vs playback args ---
SERVER_ARGS=()
WAV_FILE="test.wav"
NEXT_IS_FILE=0

# Process all arguments
i=0
while [ $i -lt $# ]; do
  i=$((i+1))
  arg="${!i}"
  
  if [ "$NEXT_IS_FILE" = 1 ]; then
    WAV_FILE="$arg"
    NEXT_IS_FILE=0
    continue
  fi
  
  case "$arg" in
    --file)
      NEXT_IS_FILE=1
      ;;
    --file=*)
      WAV_FILE="${arg#*=}"
      ;;
    --host=*)
      SERVER_ARGS+=("$arg")
      HOST="${arg#*=}"
      ;;
    --host)
      j=$((i+1))
      if [ $j -le $# ]; then
        SERVER_ARGS+=("$arg" "${!j}")
        HOST="${!j}"
        i=$j
      fi
      ;;
    --port=*)
      SERVER_ARGS+=("$arg")
      PORT="${arg#*=}"
      ;;
    --port)
      j=$((i+1))
      if [ $j -le $# ]; then
        SERVER_ARGS+=("$arg" "${!j}")
        PORT="${!j}"
        i=$j
      fi
      ;;
    *)
      SERVER_ARGS+=("$arg")
      ;;
  esac
done

# Set defaults if not specified
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8081}"

cd "$EXAMPLES_DIR"
echo "[LOG] Starting MCP server (llm_hardware_control.py) in background..."
python3 "$SERVER_SCRIPT" "${SERVER_ARGS[@]}" >../server_stdout.log 2>../server_stderr.log &
SERVER_PID=$!
echo "[LOG] MCP server started with PID $SERVER_PID. Logs: ../server_stdout.log ../server_stderr.log"

# Wait for server to become ready (TCP connection test)
echo "[LOG] Waiting for MCP server to become ready..."

# If HOST is 0.0.0.0, test on 127.0.0.1
TEST_HOST="$HOST"
if [ "$HOST" = "0.0.0.0" ]; then
  TEST_HOST="127.0.0.1"
fi

echo "[LOG] Testing MCP server availability at $TEST_HOST:$PORT ..."
TRIES=20
SLEEP=1
READY=0

for i in $(seq 1 $TRIES); do
  if nc -z "$TEST_HOST" "$PORT"; then
    READY=1
    echo "[LOG] MCP server is ready (connection succeeded)."
    break
  fi
  sleep $SLEEP
done

if [ $READY -eq 0 ]; then
  echo "[ERROR] MCP server did not become ready at $TEST_HOST:$PORT after $((TRIES * SLEEP)) seconds." >&2
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

echo "[LOG] MCP server is ready. Proceeding to playback."

# Play WAV file on RPI host after server is ready
echo "[LOG] Checking WAV file: ../examples/$WAV_FILE"
if [ ! -f "../examples/$WAV_FILE" ]; then
  echo "[ERROR] WAV file '../examples/$WAV_FILE' not found." >&2
  kill $SERVER_PID 2>/dev/null || true
  exit 2
fi

echo "[LOG] Sending $WAV_FILE to MCP server for playback using speaker_control.py..."
# Use the same HOST/PORT for client connection that we used for server
if [ "$HOST" = "0.0.0.0" ]; then
  CLIENT_HOST="127.0.0.1"  # For local connections to 0.0.0.0
else
  CLIENT_HOST="$HOST"
fi

echo "[LOG] Using client connection: $CLIENT_HOST:$PORT"

# Create a temporary .env file with the correct connection settings
TMP_ENV_FILE="../.env.tmp"
echo "RPI_HOST=$CLIENT_HOST" > "$TMP_ENV_FILE"
echo "RPI_PORT=$PORT" >> "$TMP_ENV_FILE"

# Use the temporary .env file for the client
DOTENV_PATH="$TMP_ENV_FILE" python3 speaker_control.py --file "$WAV_FILE" --remote >../playback_stdout.log 2>../playback_stderr.log
PLAYBACK_STATUS=$?

# Clean up
rm -f "$TMP_ENV_FILE"

echo "[LOG] Playback script exited with status $PLAYBACK_STATUS. See ../playback_stdout.log ../playback_stderr.log for details."

# Optionally stop the server
echo "[LOG] Stopping MCP server (PID $SERVER_PID)..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
echo "[LOG] MCP server stopped."
