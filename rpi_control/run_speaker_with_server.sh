#!/bin/bash
# Script to run the simplified server and client for audio playback

# Default values
HOST="0.0.0.0"
PORT=8081
FILE="test.wav"
LOG_FILE="speaker_script.log"
SERVER_LOG="server.log"
CLIENT_LOG="client.log"

# Function to log messages with timestamp
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to log system information
log_system_info() {
    log "INFO" "=== SYSTEM INFORMATION ==="
    log "INFO" "Hostname: $(hostname)"
    log "INFO" "OS: $(uname -a)"
    log "INFO" "IP Addresses:"
    ip -4 addr show | grep inet | awk '{print "  - " $2}' | while read -r line; do
        log "INFO" "$line"
    done
    
    # Check for audio devices
    log "INFO" "Audio devices:"
    if command -v aplay &> /dev/null; then
        aplay -l | while read -r line; do
            log "INFO" "  $line"
        done
    else
        log "WARNING" "  aplay command not found, cannot list audio devices"
    fi
    
    # Check for Python version
    log "INFO" "Python version: $(python3 --version 2>&1)"
    
    # Check disk space
    log "INFO" "Disk space:"
    df -h . | while read -r line; do
        log "INFO" "  $line"
    done
    
    log "INFO" "=== END SYSTEM INFORMATION ==="
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --file)
            FILE="$2"
            shift 2
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            echo "Usage: $0 [--host HOST] [--port PORT] [--file FILE]"
            exit 1
            ;;
    esac
done

# Initialize log file
> "$LOG_FILE"
log "INFO" "Starting run_speaker_with_server.sh script"
log "INFO" "Using server: $HOST:$PORT, client will connect to: 127.0.0.1:$PORT"

# Log system information
log_system_info

# Check if the audio file exists, if not and it's test.wav, create a test tone
if [[ ! -f "$FILE" && "$FILE" == "test.wav" ]]; then
    log "INFO" "Generating test audio file: $FILE"
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" -ac 1 "$FILE" -y &> /dev/null
        if [[ $? -eq 0 ]]; then
            log "INFO" "Generated test audio file: $FILE"
        else
            log "ERROR" "Failed to generate test audio file"
            exit 1
        fi
    else
        log "ERROR" "ffmpeg not found, cannot generate test audio file"
        exit 1
    fi
fi

# Verify the file exists now
if [[ ! -f "$FILE" ]]; then
    log "ERROR" "Audio file not found: $FILE"
    exit 1
fi

log "INFO" "Audio file details: $(ls -lh "$FILE" | awk '{print $5, $6, $7, $8}')"

# Function to check if server is running
check_server() {
    if command -v nc &> /dev/null; then
        nc -z 127.0.0.1 "$PORT" &> /dev/null
        return $?
    elif command -v python3 &> /dev/null; then
        python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1', $PORT)); s.close()" &> /dev/null
        return $?
    else
        log "ERROR" "Neither nc nor python3 available to check server"
        return 1
    fi
}

# Check if server is already running
SERVER_STARTED=false
if check_server; then
    log "INFO" "Server already running on port $PORT"
else
    # Start the server
    log "INFO" "Starting simplified server at $HOST:$PORT..."
    
    # Clear previous server log
    > "$SERVER_LOG"
    
    # Start server in background
    python3 examples/simple_server.py --host "$HOST" --port "$PORT" > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    
    # Check if server process is running
    if ps -p $SERVER_PID > /dev/null; then
        log "INFO" "Server started with PID $SERVER_PID, logs in $SERVER_LOG"
        SERVER_STARTED=true
    else
        log "ERROR" "Failed to start server"
        exit 1
    fi
    
    # Wait for server to become ready
    log "INFO" "Waiting for server to become ready..."
    TIMEOUT=30
    ELAPSED=0
    while ! check_server && [[ $ELAPSED -lt $TIMEOUT ]]; do
        sleep 1
        ((ELAPSED++))
        
        # Show server log progress
        if [[ -f "$SERVER_LOG" ]]; then
            NEW_LOGS=$(tail -n 5 "$SERVER_LOG" | grep -v "^$")
            if [[ ! -z "$NEW_LOGS" ]]; then
                log "SERVER" "Recent logs:"
                echo "$NEW_LOGS" | while read -r line; do
                    log "SERVER" "  $line"
                done
            fi
        fi
        
        # Check if server is still running
        if ! ps -p $SERVER_PID > /dev/null; then
            log "ERROR" "Server process died unexpectedly"
            if [[ -f "$SERVER_LOG" ]]; then
                log "ERROR" "Server log:"
                cat "$SERVER_LOG" | while read -r line; do
                    log "ERROR" "  $line"
                done
            fi
            exit 1
        fi
    done
    
    if [[ $ELAPSED -ge $TIMEOUT ]]; then
        log "ERROR" "Timeout waiting for server to become ready"
        kill -9 $SERVER_PID 2>/dev/null
        exit 1
    fi
    
    log "INFO" "Server is ready."
fi

# Clear previous client log
> "$CLIENT_LOG"

# Play the audio file
log "INFO" "Playing $FILE on server..."
python3 examples/simple_client.py --host "127.0.0.1" --port "$PORT" --file "$FILE" --remote > "$CLIENT_LOG" 2>&1
CLIENT_EXIT=$?

# Show client logs
if [[ -f "$CLIENT_LOG" ]]; then
    log "INFO" "Client logs:"
    cat "$CLIENT_LOG" | while read -r line; do
        log "CLIENT" "  $line"
    done
fi

# Check client exit status
if [[ $CLIENT_EXIT -eq 0 ]]; then
    log "INFO" "Playback request sent successfully."
else
    log "ERROR" "Playback request failed with exit code $CLIENT_EXIT"
fi

# Stop the server if we started it
if [[ "$SERVER_STARTED" = true ]]; then
    log "INFO" "Stopping server (PID $SERVER_PID)"
    kill $SERVER_PID 2>/dev/null
    
    # Wait for server to stop
    TIMEOUT=10
    ELAPSED=0
    while ps -p $SERVER_PID > /dev/null && [[ $ELAPSED -lt $TIMEOUT ]]; do
        sleep 1
        ((ELAPSED++))
    done
    
    if ps -p $SERVER_PID > /dev/null; then
        log "WARNING" "Server did not stop gracefully, forcing..."
        kill -9 $SERVER_PID 2>/dev/null
    fi
fi

log "INFO" "Script completed"
exit $CLIENT_EXIT
