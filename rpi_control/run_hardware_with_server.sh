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
    # Try to connect to the server on the remote host
    TIMEOUT=2
    ssh -o ConnectTimeout=$TIMEOUT "$REMOTE_USER@$REMOTE_HOST" "nc -z -w $TIMEOUT 127.0.0.1 $PORT" 2>/dev/null
    return $?
}

# Function to check if it's our hardware server running on remote host
check_hardware_server() {
    # Try to send a ping command to verify it's our hardware server
    PING_RESULT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 -c \"
import socket
import json
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(('127.0.0.1', $PORT))
    s.send(json.dumps({'action': 'ping'}).encode())
    data = s.recv(1024).decode()
    s.close()
    print(data)
except Exception as e:
    print('ERROR: ' + str(e))
\"" 2>/dev/null)
    
    if [[ "$PING_RESULT" == *"pong"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to run server locally
run_local_server() {
    # Check if server is already running
    SERVER_STARTED=false
    if check_local_server; then
        log "INFO" "Server already running on port $PORT"
    else
        # Start the server
        log "INFO" "Starting hardware server at $HOST:$PORT..."
        
        # Clear previous server log
        > "$SERVER_LOG"
        
        # Start server in background
        python3 examples/hardware_server.py --host "$HOST" --port "$PORT" > "$SERVER_LOG" 2>&1 &
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

    # Send the hardware command
    log "INFO" "Sending command '$COMMAND' to server..."
    
    # Build the command arguments
    CLIENT_ARGS="--host 127.0.0.1 --port $PORT --command $COMMAND"
    
    # Add command-specific arguments
    if [[ "$COMMAND" == "gpio" ]]; then
        if [[ -z "$PIN" || -z "$STATE" ]]; then
            log "ERROR" "GPIO command requires --pin and --state arguments"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --pin $PIN --state $STATE"
    elif [[ "$COMMAND" == "i2c" ]]; then
        if [[ -z "$ADDRESS" || -z "$REGISTER" ]]; then
            log "ERROR" "I2C command requires --address and --register arguments"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --address $ADDRESS --register $REGISTER"
        if [[ -n "$VALUE" ]]; then
            CLIENT_ARGS="$CLIENT_ARGS --value $VALUE"
        fi
    fi
    
    # Run the client with the built arguments
    python3 examples/hardware_client.py $CLIENT_ARGS > "$CLIENT_LOG" 2>&1
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
        log "INFO" "Command request sent successfully."
    else
        log "ERROR" "Command request failed with exit code $CLIENT_EXIT"
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
    
    # Start the server on remote host and get its PID directly
    log "INFO" "Starting server on remote host at $HOST:$PORT"
    REMOTE_SERVER_PID=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_server.py --host '$HOST' --port '$PORT' > server.log 2>&1 & echo \$!")
    
    if [[ -z "$REMOTE_SERVER_PID" || "$REMOTE_SERVER_PID" == "0" ]]; then
        log "ERROR" "Failed to start server on remote host"
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
    
    # Wait for server to become ready
    log "INFO" "Waiting for server to become ready on remote host..."
    TIMEOUT=10
    ELAPSED=0
    SERVER_READY=false
    
    while [[ $ELAPSED -lt $TIMEOUT && "$SERVER_READY" = false ]]; do
        # Check if server is listening on the port
        if ssh "$REMOTE_USER@$REMOTE_HOST" "nc -z -w 1 127.0.0.1 $PORT" 2>/dev/null; then
            log "INFO" "Server is listening on port $PORT"
            SERVER_READY=true
        else
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
        fi
    done
    
    if [[ "$SERVER_READY" = false ]]; then
        log "ERROR" "Timeout waiting for server to become ready on remote host"
        ssh "$REMOTE_USER@$REMOTE_HOST" "kill -9 $REMOTE_SERVER_PID 2>/dev/null"
        exit 1
    fi
    
    log "INFO" "Server is ready on remote host"
    
    # Send the hardware command on remote host
    log "INFO" "Sending command '$COMMAND' on remote server..."
    
    # Build the command arguments
    CLIENT_ARGS="--host 127.0.0.1 --port $PORT --command $COMMAND"
    
    # Add command-specific arguments
    if [[ "$COMMAND" == "gpio" ]]; then
        if [[ -z "$PIN" || -z "$STATE" ]]; then
            log "ERROR" "GPIO command requires --pin and --state arguments"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --pin $PIN --state $STATE"
    elif [[ "$COMMAND" == "i2c" ]]; then
        if [[ -z "$ADDRESS" || -z "$REGISTER" ]]; then
            log "ERROR" "I2C command requires --address and --register arguments"
            exit 1
        fi
        CLIENT_ARGS="$CLIENT_ARGS --address $ADDRESS --register $REGISTER"
        if [[ -n "$VALUE" ]]; then
            CLIENT_ARGS="$CLIENT_ARGS --value $VALUE"
        fi
    fi
    
    # Run the client with the built arguments and capture both stdout and stderr
    log "INFO" "Running command on remote host: python3 hardware_client.py $CLIENT_ARGS"
    REMOTE_CLIENT_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py $CLIENT_ARGS" 2>&1)
    REMOTE_EXIT_CODE=$?
    
    if [[ $REMOTE_EXIT_CODE -ne 0 ]]; then
        log "ERROR" "Failed to run client on remote host (exit code: $REMOTE_EXIT_CODE)"
        log "ERROR" "Remote output:"
        echo "$REMOTE_CLIENT_OUTPUT" | while read -r line; do
            log "ERROR" "  $line"
        done
        
        # Check if Python exists on the remote host
        log "INFO" "Checking Python on remote host..."
        PYTHON_VERSION=$(ssh "$REMOTE_USER@$REMOTE_HOST" "python3 --version" 2>&1)
        log "INFO" "Remote Python: $PYTHON_VERSION"
        
        # Check if the client script exists on the remote host
        log "INFO" "Checking if client script exists on remote host..."
        SCRIPT_EXISTS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "ls -la $REMOTE_DIR/hardware_client.py" 2>&1)
        log "INFO" "Client script: $SCRIPT_EXISTS"
        
        exit 1
    fi
    
    # Get client logs from remote host
    log "INFO" "Remote client output:"
    echo "$REMOTE_CLIENT_OUTPUT" | while read -r line; do
        log "REMOTE_CLIENT" "  $line"
    done
    
    log "INFO" "Command request sent successfully to remote host."
    
    return 0
}

# Function to send GPIO commands to toggle pin state
toggle_gpio_pins() {
    local pin="$1"
    
    if [[ -z "$pin" ]]; then
        log "ERROR" "No GPIO pin specified for toggling"
        return 1
    fi
    
    log "INFO" "Toggling GPIO pin $pin state twice..."
    
    # First set the pin to HIGH
    log "INFO" "Setting GPIO pin $pin to HIGH"
    if [[ "$LOCAL_MODE" = true ]]; then
        python3 "examples/hardware_client.py" --host "$HOST" --port "$PORT" --command "gpio" --pin "$pin" --state "on" > "$CLIENT_LOG" 2>&1
    else
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py --host 127.0.0.1 --port $PORT --command gpio --pin $pin --state on" 2>&1
    fi
    
    # Wait a second
    sleep 1
    
    # Then set the pin to LOW
    log "INFO" "Setting GPIO pin $pin to LOW"
    if [[ "$LOCAL_MODE" = true ]]; then
        python3 "examples/hardware_client.py" --host "$HOST" --port "$PORT" --command "gpio" --pin "$pin" --state "off" > "$CLIENT_LOG" 2>&1
    else
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 hardware_client.py --host 127.0.0.1 --port $PORT --command gpio --pin $pin --state off" 2>&1
    fi
    
    log "INFO" "GPIO pin $pin toggled twice successfully"
    return 0
}

# Run in local or remote mode
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
    
    # If command is status, also toggle GPIO pins from .env
    if [[ "$COMMAND" == "status" ]]; then
        # Get GPIO pin from .env or use default
        GPIO_PIN=${GPIO_PIN:-17}
        log "INFO" "Status command completed, now toggling GPIO pin $GPIO_PIN"
        toggle_gpio_pins "$GPIO_PIN"
    fi
fi

log "INFO" "Script completed"
exit 0
