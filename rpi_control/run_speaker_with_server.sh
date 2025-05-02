#!/bin/bash
# Script to run the simplified server and client for audio playback
# Supports both local and remote execution
clear
# Default values
HOST="0.0.0.0"
PORT=8081
FILE="test.wav"
LOG_FILE="speaker_script.log"
SERVER_LOG="server.log"
CLIENT_LOG="client.log"
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_DIR="/tmp/audio_server"
LOCAL_MODE=true

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    log() {
        local level="$1"
        local message="$2"
        local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        echo "[$timestamp] [$level] $message"
    }
    
    log "INFO" "Loading configuration from .env file"
    
    # Source the .env file
    source .env
    
    # Use values from .env if they exist
    [[ -n "$RPI_HOST" ]] && REMOTE_HOST="$RPI_HOST"
    [[ -n "$RPI_USERNAME" ]] && REMOTE_USER="$RPI_USERNAME"
    [[ -n "$RPI_PORT" ]] && PORT="$RPI_PORT"
    [[ -n "$DEFAULT_WAV" ]] && FILE="$DEFAULT_WAV"
    [[ -n "$REMOTE_PATH" ]] && REMOTE_DIR="$REMOTE_PATH/audio_server"
    
    # If REMOTE is set in format user@host, extract user and host
    if [[ -n "$REMOTE" && "$REMOTE" == *"@"* ]]; then
        REMOTE_USER="${REMOTE%%@*}"
        REMOTE_HOST="${REMOTE##*@}"
    fi
    
    # If both REMOTE_HOST and REMOTE_USER are set from .env, use remote mode
    if [[ -n "$REMOTE_HOST" && -n "$REMOTE_USER" ]]; then
        LOCAL_MODE=false
    fi
fi

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

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --host HOST             Host to bind the server to (default: 0.0.0.0)"
    echo "  --port PORT             Port to use for the server (default: $PORT from .env or 8081)"
    echo "  --file FILE             Audio file to play (default: $FILE from .env or test.wav)"
    echo "  --remote-host HOST      Remote host to run the server on (default: $REMOTE_HOST from .env)"
    echo "  --remote-user USER      Username for SSH connection to remote host (default: $REMOTE_USER from .env)"
    echo "  --remote-dir DIR        Directory on remote host to use (default: $REMOTE_DIR)"
    echo "  --local                 Force local mode even if remote settings exist in .env"
    echo "  --help                  Show this help message"
    echo ""
    echo "Note: This script will use values from .env file if present."
    exit 0
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
        --remote-host)
            REMOTE_HOST="$2"
            LOCAL_MODE=false
            shift 2
            ;;
        --remote-user)
            REMOTE_USER="$2"
            shift 2
            ;;
        --remote-dir)
            REMOTE_DIR="$2"
            shift 2
            ;;
        --local)
            LOCAL_MODE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            echo "Usage: $0 [--host HOST] [--port PORT] [--file FILE] [--remote-host HOST] [--remote-user USER] [--remote-dir DIR] [--local]"
            exit 1
            ;;
    esac
done

# Check if remote host is specified but user is not
if [[ "$LOCAL_MODE" == "false" && -z "$REMOTE_USER" ]]; then
    log "ERROR" "Remote host specified but remote user is missing. Use --remote-user to specify."
    exit 1
fi

# Initialize log file
> "$LOG_FILE"
log "INFO" "Starting run_speaker_with_server.sh script"

if [[ "$LOCAL_MODE" == true ]]; then
    log "INFO" "Running in LOCAL mode"
    log "INFO" "Using server: $HOST:$PORT, client will connect to: 127.0.0.1:$PORT"
else
    log "INFO" "Running in REMOTE mode"
    log "INFO" "Remote host: $REMOTE_USER@$REMOTE_HOST"
    log "INFO" "Remote directory: $REMOTE_DIR"
    log "INFO" "Server will run on remote host at $HOST:$PORT"
fi

# Log system information
log_system_info

# Function to check if server is running locally
check_local_server() {
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

# Function to check if server is running on remote host
check_remote_server() {
    ssh "$REMOTE_USER@$REMOTE_HOST" "if command -v nc &> /dev/null; then nc -z 127.0.0.1 $PORT &> /dev/null; echo \$?; else python3 -c \"import socket; s=socket.socket(); s.connect(('127.0.0.1', $PORT)); s.close(); print(0)\" 2>/dev/null || echo 1; fi" | grep -q "0"
    return $?
}

# Function to prepare audio file
prepare_audio_file() {
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
}

# Function to run server locally
run_local_server() {
    # Check if server is already running
    SERVER_STARTED=false
    if check_local_server; then
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
        while ! check_local_server && [[ $ELAPSED -lt $TIMEOUT ]]; do
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

    return $CLIENT_EXIT
}

# Function to run server on remote host
run_remote_server() {
    # Create remote directory if it doesn't exist
    log "INFO" "Creating remote directory: $REMOTE_DIR"
    ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR" || {
        log "ERROR" "Failed to create remote directory"
        exit 1
    }
    
    # Copy necessary files to remote host
    log "INFO" "Copying server script to remote host"
    scp "examples/simple_server.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy server script"
        exit 1
    }
    
    log "INFO" "Copying client script to remote host"
    scp "examples/simple_client.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy client script"
        exit 1
    }
    
    log "INFO" "Copying audio file to remote host"
    scp "$FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy audio file"
        exit 1
    }
    
    # Check if server is already running on remote host
    SERVER_STARTED=false
    if check_remote_server; then
        log "INFO" "Server already running on remote host at port $PORT"
    else
        # Start the server on remote host
        log "INFO" "Starting server on remote host at $HOST:$PORT"
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 simple_server.py --host '$HOST' --port '$PORT' > server.log 2>&1 &" || {
            log "ERROR" "Failed to start server on remote host"
            exit 1
        }
        
        # Get server PID
        REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "pgrep -f 'python3.*simple_server.py'")
        if [[ -z "$REMOTE_SERVER_PID" ]]; then
            log "ERROR" "Failed to get server PID on remote host"
            exit 1
        fi
        
        log "INFO" "Server started on remote host with PID $REMOTE_SERVER_PID"
        SERVER_STARTED=true
        
        # Wait for server to become ready
        log "INFO" "Waiting for server to become ready on remote host..."
        TIMEOUT=30
        ELAPSED=0
        while ! check_remote_server && [[ $ELAPSED -lt $TIMEOUT ]]; do
            sleep 1
            ((ELAPSED++))
            
            # Show remote server log progress
            REMOTE_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then tail -n 5 '$REMOTE_DIR/server.log' | grep -v '^$'; fi")
            if [[ ! -z "$REMOTE_LOGS" ]]; then
                log "REMOTE_SERVER" "Recent logs:"
                echo "$REMOTE_LOGS" | while read -r line; do
                    log "REMOTE_SERVER" "  $line"
                done
            fi
            
            # Check if server is still running on remote host
            if ! ssh "$REMOTE_USER@$REMOTE_HOST" "ps -p $REMOTE_SERVER_PID > /dev/null"; then
                log "ERROR" "Server process died unexpectedly on remote host"
                REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then cat '$REMOTE_DIR/server.log'; fi")
                if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
                    log "ERROR" "Remote server log:"
                    echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                        log "ERROR" "  $line"
                    done
                fi
                exit 1
            fi
        done
        
        if [[ $ELAPSED -ge $TIMEOUT ]]; then
            log "ERROR" "Timeout waiting for server to become ready on remote host"
            ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
            exit 1
        fi
        
        log "INFO" "Server is ready on remote host."
    fi
    
    # Get the filename without path
    FILENAME=$(basename "$FILE")
    
    # Play the audio file on remote host
    log "INFO" "Playing $FILENAME on remote server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 simple_client.py --host '127.0.0.1' --port '$PORT' --file '$FILENAME' --remote > client.log 2>&1" || {
        log "ERROR" "Failed to run client on remote host"
        exit 1
    }
    
    # Get client logs from remote host
    REMOTE_CLIENT_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/client.log' ]]; then cat '$REMOTE_DIR/client.log'; fi")
    if [[ ! -z "$REMOTE_CLIENT_LOGS" ]]; then
        log "INFO" "Remote client logs:"
        echo "$REMOTE_CLIENT_LOGS" | while read -r line; do
            log "REMOTE_CLIENT" "  $line"
        done
    fi
    
    log "INFO" "Playback request sent successfully to remote host."
    
    # Stop the server if we started it
    if [[ "$SERVER_STARTED" = true ]]; then
        log "INFO" "Stopping server on remote host (PID $REMOTE_SERVER_PID)"
        ssh "$REMOTE_USER@$REMOTE_HOST" "kill $REMOTE_SERVER_PID 2>/dev/null" || {
            log "WARNING" "Failed to stop server gracefully on remote host"
            ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
        }
    fi
    
    return 0
}

# Prepare audio file
prepare_audio_file

# Run in local or remote mode
if [[ "$LOCAL_MODE" == true ]]; then
    run_local_server
    EXIT_CODE=$?
else
    run_remote_server
    EXIT_CODE=$?
fi

log "INFO" "Script completed"
exit $EXIT_CODE
