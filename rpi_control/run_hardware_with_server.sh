#!/bin/bash
# Script to run hardware control server and client
# Supports both local and remote execution
clear
# Function to log messages with timestamp
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message"
    if [[ -n "$LOG_FILE" ]]; then
        echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    fi
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
    
    # Check for GPIO access (if on Raspberry Pi)
    if [[ -d "/sys/class/gpio" ]]; then
        log "INFO" "GPIO access available: Yes"
    else
        log "INFO" "GPIO access available: No"
    fi
    
    # Check for I2C devices
    if command -v i2cdetect &> /dev/null; then
        log "INFO" "I2C devices:"
        i2cdetect -l | while read -r line; do
            log "INFO" "  $line"
        done
    else
        log "INFO" "I2C tools not available"
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
    echo "  --port PORT             Port to use for the server (default: $PORT from .env or 8082)"
    echo "  --command COMMAND       Hardware command to execute (default: status)"
    echo "  --pin PIN               GPIO pin number (for gpio command)"
    echo "  --state STATE           GPIO pin state (on/off, for gpio command)"
    echo "  --address ADDRESS       I2C device address (for i2c command)"
    echo "  --register REGISTER     I2C register (for i2c command)"
    echo "  --value VALUE           I2C value to write (for i2c command)"
    echo "  --remote-host HOST      Remote host to run the server on (default: $REMOTE_HOST from .env)"
    echo "  --remote-user USER      Username for SSH connection to remote host (default: $REMOTE_USER from .env)"
    echo "  --remote-dir DIR        Directory on remote host to use (default: $REMOTE_DIR)"
    echo "  --local                 Force local mode even if remote settings exist in .env"
    echo "  --help                  Show this help message"
    echo ""
    echo "Note: This script will use values from .env file if present."
    exit 0
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
    scp "examples/hardware_server.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy server script"
        exit 1
    }
    
    log "INFO" "Copying client script to remote host"
    scp "examples/hardware_client.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy client script"
        exit 1
    }
    
    # Kill any existing process on the port
    log "INFO" "Ensuring port $PORT is free on remote host"
    ssh "$REMOTE_USER@$REMOTE_HOST" "fuser -k $PORT/tcp 2>/dev/null || true" 
    sleep 2
    
    # Create a simple startup script on the remote host
    log "INFO" "Creating startup script on remote host"
    cat > /tmp/start_server.sh << EOF
#!/bin/bash
cd $REMOTE_DIR
# Use nohup to ensure the server keeps running even if the SSH session ends
nohup python3 hardware_server.py --host '$HOST' --port '$PORT' > server.log 2>&1 &
echo \$! > server.pid
# Give the server a moment to start
sleep 2
# Verify the server is running
if ! ps -p \$(cat server.pid) > /dev/null; then
  echo "Server failed to start" >&2
  exit 1
fi
# Verify the server is listening on the port
for i in {1..5}; do
  if nc -z -w 1 127.0.0.1 $PORT; then
    echo "Server is listening on port $PORT"
    exit 0
  fi
  sleep 1
done
echo "Server is not listening on port $PORT after 5 seconds" >&2
exit 1
EOF
    
    # Copy the startup script to the remote host
    scp /tmp/start_server.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" || {
        log "ERROR" "Failed to copy startup script"
        exit 1
    }
    
    # Make the script executable
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/start_server.sh" || {
        log "ERROR" "Failed to make startup script executable"
        exit 1
    }
    
    # Start the server using the script
    log "INFO" "Starting server on remote host at $HOST:$PORT"
    SERVER_START_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "$REMOTE_DIR/start_server.sh" 2>&1)
    SERVER_START_EXIT_CODE=$?
    
    if [[ $SERVER_START_EXIT_CODE -ne 0 ]]; then
        log "ERROR" "Failed to start server (exit code: $SERVER_START_EXIT_CODE)"
        log "ERROR" "Server startup output:"
        echo "$SERVER_START_OUTPUT" | while read -r line; do
            log "ERROR" "  $line"
        done
        exit 1
    else
        log "INFO" "Server startup output:"
        echo "$SERVER_START_OUTPUT" | while read -r line; do
            log "INFO" "  $line"
        done
    fi
    
    # Get the server PID from the pid file
    REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cat $REMOTE_DIR/server.pid 2>/dev/null")
    
    if [[ -z "$REMOTE_SERVER_PID" ]]; then
        log "ERROR" "Failed to get server PID from pid file"
        # Show any error logs
        REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then cat '$REMOTE_DIR/server.log'; fi")
        if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
            log "ERROR" "Remote server log:"
            echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                log "ERROR" "  $line"
            done
        fi
        exit 1
    fi
    
    log "INFO" "Server started on remote host with PID $REMOTE_SERVER_PID"
    
    # Check if server is listening on the port (with timeout)
    log "INFO" "Checking if server is listening on port $PORT..."
    TIMEOUT=10
    for ((i=1; i<=TIMEOUT; i++)); do
        if ssh "$REMOTE_USER@$REMOTE_HOST" "nc -z -w 1 127.0.0.1 $PORT" 2>/dev/null; then
            log "INFO" "Server is listening on port $PORT"
            break
        fi
        
        if [[ $i -eq $TIMEOUT ]]; then
            log "ERROR" "Timeout waiting for server to listen on port $PORT"
            ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
            # Show any error logs
            REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then cat '$REMOTE_DIR/server.log'; fi")
            if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
                log "ERROR" "Remote server log:"
                echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                    log "ERROR" "  $line"
                done
            fi
            exit 1
        fi
        
        log "INFO" "Waiting for server to listen on port $PORT (attempt $i/$TIMEOUT)..."
        sleep 1
    done
    
    # Execute the command
    log "INFO" "Executing command '$COMMAND' on remote host..."
    
    # Build command arguments
    CLIENT_ARGS="--host 127.0.0.1 --port $PORT --command $COMMAND"
    
    # Add command-specific arguments
    if [[ "$COMMAND" == "gpio" ]]; then
        if [[ -z "$PIN" || -z "$STATE" ]]; then
            log "ERROR" "GPIO command requires --pin and --state arguments"
            ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --pin $PIN --state $STATE"
    elif [[ "$COMMAND" == "i2c" ]]; then
        if [[ -z "$ADDRESS" || -z "$REGISTER" ]]; then
            log "ERROR" "I2C command requires --address and --register arguments"
            ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --address $ADDRESS --register $REGISTER"
        if [[ -n "$VALUE" ]]; then
            CLIENT_ARGS="$CLIENT_ARGS --value $VALUE"
        fi
    fi
    
    # Execute the command
    log "INFO" "Running command: python3 hardware_client.py $CLIENT_ARGS"
    COMMAND_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py $CLIENT_ARGS" 2>&1)
    COMMAND_EXIT_CODE=$?
    
    if [[ $COMMAND_EXIT_CODE -ne 0 ]]; then
        log "ERROR" "Command failed with exit code $COMMAND_EXIT_CODE"
        log "ERROR" "Command output:"
        echo "$COMMAND_OUTPUT" | while read -r line; do
            log "ERROR" "  $line"
        done
        ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
        exit 1
    fi
    
    # Display command output
    log "INFO" "Command output:"
    echo "$COMMAND_OUTPUT" | while read -r line; do
        log "COMMAND" "  $line"
    done
    
    # If command is status, toggle GPIO pin
    if [[ "$COMMAND" == "status" && -n "$PIN" ]]; then
        log "INFO" "Status command completed, toggling GPIO pin $PIN"
        
        # Verify server is still running
        if ! ssh "$REMOTE_USER@$REMOTE_HOST" "ps -p $REMOTE_SERVER_PID > /dev/null 2>&1"; then
            log "ERROR" "Server process is no longer running, restarting..."
            SERVER_START_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "$REMOTE_DIR/start_server.sh" 2>&1)
            SERVER_START_EXIT_CODE=$?
            
            if [[ $SERVER_START_EXIT_CODE -ne 0 ]]; then
                log "ERROR" "Failed to restart server (exit code: $SERVER_START_EXIT_CODE)"
                log "ERROR" "Server restart output:"
                echo "$SERVER_START_OUTPUT" | while read -r line; do
                    log "ERROR" "  $line"
                done
                exit 1
            fi
            
            REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cat $REMOTE_DIR/server.pid 2>/dev/null")
            log "INFO" "Server restarted with PID $REMOTE_SERVER_PID"
        fi
        
        # Set pin HIGH with retry mechanism
        log "INFO" "Setting GPIO pin $PIN to HIGH"
        MAX_RETRIES=3
        for ((retry=1; retry<=MAX_RETRIES; retry++)); do
            GPIO_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py --host 127.0.0.1 --port $PORT --command gpio --pin $PIN --state on" 2>&1)
            GPIO_EXIT_CODE=$?
            
            if [[ $GPIO_EXIT_CODE -eq 0 ]]; then
                log "SUCCESS" "GPIO pin $PIN set to HIGH"
                echo "$GPIO_OUTPUT" | while read -r line; do
                    log "GPIO_HIGH" "  $line"
                done
                break
            else
                log "WARNING" "Attempt $retry/$MAX_RETRIES: Failed to set GPIO pin $PIN to HIGH (exit code: $GPIO_EXIT_CODE)"
                
                if [[ $retry -eq $MAX_RETRIES ]]; then
                    log "ERROR" "All attempts to set GPIO pin $PIN to HIGH failed"
                    log "ERROR" "Last output: $GPIO_OUTPUT"
                    
                    # Check server logs for any issues
                    REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then tail -n 20 '$REMOTE_DIR/server.log'; fi")
                    if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
                        log "ERROR" "Recent server logs:"
                        echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                            log "ERROR" "  $line"
                        done
                    fi
                else
                    # Verify server is still running before retry
                    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "ps -p $REMOTE_SERVER_PID > /dev/null 2>&1"; then
                        log "WARNING" "Server process died, restarting before retry..."
                        ssh "$REMOTE_USER@$REMOTE_HOST" "$REMOTE_DIR/start_server.sh" > /dev/null 2>&1
                        REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cat $REMOTE_DIR/server.pid 2>/dev/null")
                        log "INFO" "Server restarted with PID $REMOTE_SERVER_PID"
                    fi
                    log "INFO" "Retrying in 2 seconds..."
                    sleep 2
                fi
            fi
        done
        
        sleep 1
        
        # Set pin LOW with retry mechanism
        log "INFO" "Setting GPIO pin $PIN to LOW"
        for ((retry=1; retry<=MAX_RETRIES; retry++)); do
            GPIO_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py --host 127.0.0.1 --port $PORT --command gpio --pin $PIN --state off" 2>&1)
            GPIO_EXIT_CODE=$?
            
            if [[ $GPIO_EXIT_CODE -eq 0 ]]; then
                log "SUCCESS" "GPIO pin $PIN set to LOW"
                echo "$GPIO_OUTPUT" | while read -r line; do
                    log "GPIO_LOW" "  $line"
                done
                break
            else
                log "WARNING" "Attempt $retry/$MAX_RETRIES: Failed to set GPIO pin $PIN to LOW (exit code: $GPIO_EXIT_CODE)"
                
                if [[ $retry -eq $MAX_RETRIES ]]; then
                    log "ERROR" "All attempts to set GPIO pin $PIN to LOW failed"
                    log "ERROR" "Last output: $GPIO_OUTPUT"
                    
                    # Check server logs for any issues
                    REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then tail -n 20 '$REMOTE_DIR/server.log'; fi")
                    if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
                        log "ERROR" "Recent server logs:"
                        echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                            log "ERROR" "  $line"
                        done
                    fi
                else
                    # Verify server is still running before retry
                    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "ps -p $REMOTE_SERVER_PID > /dev/null 2>&1"; then
                        log "WARNING" "Server process died, restarting before retry..."
                        ssh "$REMOTE_USER@$REMOTE_HOST" "$REMOTE_DIR/start_server.sh" > /dev/null 2>&1
                        REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cat $REMOTE_DIR/server.pid 2>/dev/null")
                        log "INFO" "Server restarted with PID $REMOTE_SERVER_PID"
                    fi
                    log "INFO" "Retrying in 2 seconds..."
                    sleep 2
                fi
            fi
        done
        
        log "INFO" "GPIO pin $PIN toggling completed"
    fi
    
    # Stop the server
    log "INFO" "Stopping server on remote host (PID $REMOTE_SERVER_PID)"
    ssh "$REMOTE_USER@$REMOTE_HOST" "kill $REMOTE_SERVER_PID 2>/dev/null || kill -9 $REMOTE_SERVER_PID 2>/dev/null"
    
    log "INFO" "Remote server operation completed successfully"
    return 0
}

# Function to run server locally
run_local_server() {
    log "INFO" "Local server mode not fully implemented"
    return 1
}

# Default values
HOST="0.0.0.0"
LOG_FILE="hardware_script.log"
SERVER_LOG="hardware_server.log"
CLIENT_LOG="hardware_client.log"

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    log "INFO" "Loading configuration from .env file"
    source .env
fi

# Update default values with environment variables if available
PORT=${RPI_PORT:-8082}  # Use RPI_PORT from .env if available, otherwise default to 8082
COMMAND="status"
PIN=""
STATE=""
ADDRESS=""
REGISTER=""
VALUE=""
REMOTE_HOST=${RPI_HOST:-""}
REMOTE_USER=${RPI_USERNAME:-""}
REMOTE_DIR=${REMOTE_DIR:-"/tmp/hardware_server"}
LOCAL_MODE=true

# If REMOTE is set in format user@host, extract user and host
if [[ -n "$REMOTE" && "$REMOTE" == *"@"* ]]; then
    REMOTE_USER="${REMOTE%%@*}"
    REMOTE_HOST="${REMOTE##*@}"
fi

# If both REMOTE_HOST and REMOTE_USER are set from .env, use remote mode
if [[ -n "$REMOTE_HOST" && -n "$REMOTE_USER" ]]; then
    LOCAL_MODE=false
fi

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
        --command)
            COMMAND="$2"
            shift 2
            ;;
        --pin)
            PIN="$2"
            shift 2
            ;;
        --state)
            STATE="$2"
            shift 2
            ;;
        --address)
            ADDRESS="$2"
            shift 2
            ;;
        --register)
            REGISTER="$2"
            shift 2
            ;;
        --value)
            VALUE="$2"
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
            echo "Usage: $0 [--host HOST] [--port PORT] [--command COMMAND] [--remote-host HOST] [--remote-user USER] [--remote-dir DIR] [--local]"
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
log "INFO" "Starting run_hardware_with_server.sh script"

if [[ "$LOCAL_MODE" == true ]]; then
    log "INFO" "Running in LOCAL mode"
    log "INFO" "Server will run on $HOST:$PORT"
    run_local_server
else
    log "INFO" "Running in REMOTE mode"
    log "INFO" "Remote host: $REMOTE_USER@$REMOTE_HOST"
    log "INFO" "Remote directory: $REMOTE_DIR"
    log "INFO" "Server will run on remote host at $HOST:$PORT"
    log_system_info
    run_remote_server
fi

log "INFO" "Script completed"
exit 0
