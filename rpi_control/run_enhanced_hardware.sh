#!/bin/bash
# Enhanced Hardware Control Script
# Supports GPIO, I2C, LCD, Speakers, and LED Matrix
# Works in both local and remote modes

# Default values
HOST="0.0.0.0"
PORT=8082
COMMAND="status"
PIN=""
STATE=""
ADDRESS=""
REGISTER=""
VALUE=""
TEXT=""
LINE="0"
CLEAR="false"
SUB_ACTION=""
AUDIO_FILE=""
LED_ACTION=""
X=""
Y=""
LOG_FILE="hardware_script.log"
SERVER_LOG="hardware_server.log"
CLIENT_LOG="hardware_client.log"
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_DIR="/tmp/hardware_server"
LOCAL_MODE=true

# Function to log messages with timestamp
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Initialize log file
> "$LOG_FILE"
log "INFO" "Starting run_enhanced_hardware.sh script"

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    log "INFO" "Loading configuration from .env file"
    
    # Source the .env file
    source .env
    
    # Use values from .env if they exist
    [[ -n "$RPI_HOST" ]] && REMOTE_HOST="$RPI_HOST"
    [[ -n "$RPI_USERNAME" ]] && REMOTE_USER="$RPI_USERNAME"
    [[ -n "$RPI_PORT" ]] && PORT="$RPI_PORT"
    [[ -n "$GPIO_PIN" ]] && PIN="$GPIO_PIN"
    [[ -n "$I2C_ADDRESS" ]] && ADDRESS="$I2C_ADDRESS"
    [[ -n "$I2C_REGISTER" ]] && REGISTER="$I2C_REGISTER"
    [[ -n "$I2C_VALUE" ]] && VALUE="$I2C_VALUE"
    [[ -n "$LCD_TEXT" ]] && TEXT="$LCD_TEXT"
    [[ -n "$LCD_LINE" ]] && LINE="$LCD_LINE"
    [[ -n "$AUDIO_FILE" ]] && AUDIO_FILE="$AUDIO_FILE"
    [[ -n "$REMOTE_PATH" ]] && REMOTE_DIR="$REMOTE_PATH/hardware_server"
    
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

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --host HOST             Host to bind the server to (default: 0.0.0.0)"
    echo "  --port PORT             Port to use for the server (default: $PORT from .env or 8082)"
    echo "  --command COMMAND       Hardware command to execute (default: status)"
    echo "                          Available commands: status, gpio, i2c, lcd, speaker, led_matrix"
    echo ""
    echo "  GPIO Options:"
    echo "  --pin PIN               GPIO pin number (for gpio command)"
    echo "  --state STATE           GPIO pin state (on/off, for gpio command)"
    echo ""
    echo "  I2C Options:"
    echo "  --address ADDRESS       I2C device address (for i2c command)"
    echo "  --register REGISTER     I2C register (for i2c command)"
    echo "  --value VALUE           I2C value to write (for i2c command)"
    echo ""
    echo "  LCD Options:"
    echo "  --text TEXT             Text to display on LCD"
    echo "  --line LINE             LCD line number (0 or 1, default: 0)"
    echo "  --clear                 Clear the LCD display"
    echo ""
    echo "  Speaker Options:"
    echo "  --sub-action ACTION     Speaker sub-action (play_file, play_tone, speak)"
    echo "  --audio-file FILE       Audio file to play (for play_file sub-action)"
    echo ""
    echo "  LED Matrix Options:"
    echo "  --led-action ACTION     LED matrix action (clear, text, pixel)"
    echo "  --x X                   X coordinate for LED matrix"
    echo "  --y Y                   Y coordinate for LED matrix"
    echo ""
    echo "  Remote Execution Options:"
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
        --text)
            TEXT="$2"
            shift 2
            ;;
        --line)
            LINE="$2"
            shift 2
            ;;
        --clear)
            CLEAR="true"
            shift
            ;;
        --sub-action)
            SUB_ACTION="$2"
            shift 2
            ;;
        --audio-file)
            AUDIO_FILE="$2"
            shift 2
            ;;
        --led-action)
            LED_ACTION="$2"
            shift 2
            ;;
        --x)
            X="$2"
            shift 2
            ;;
        --y)
            Y="$2"
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
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Check if remote host is specified but user is not
if [[ "$LOCAL_MODE" == "false" && -z "$REMOTE_USER" ]]; then
    log "ERROR" "Remote host specified but remote user is missing. Use --remote-user to specify."
    exit 1
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
    
    # Check for GPIO access
    if [[ -d "/sys/class/gpio" ]]; then
        log "INFO" "GPIO access available: Yes"
    else
        log "INFO" "GPIO access available: No"
    fi
    
    # Check for I2C tools
    if command -v i2cdetect &> /dev/null; then
        log "INFO" "I2C tools available: Yes"
        i2cdetect -l | while read -r line; do
            log "INFO" "  $line"
        done
    else
        log "INFO" "I2C tools not available"
    fi
    
    # Check for audio devices
    log "INFO" "Audio devices:"
    if command -v aplay &> /dev/null; then
        aplay -l | while read -r line; do
            log "INFO" "  $line"
        done
    else
        log "INFO" "  aplay command not found, cannot list audio devices"
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

# Log system information
if [[ "$LOCAL_MODE" == true ]]; then
    log "INFO" "Running in LOCAL mode"
    log "INFO" "Using server: $HOST:$PORT, client will connect to: 127.0.0.1:$PORT"
else
    log "INFO" "Running in REMOTE mode"
    log "INFO" "Remote host: $REMOTE_USER@$REMOTE_HOST"
    log "INFO" "Remote directory: $REMOTE_DIR"
    log "INFO" "Server will run on remote host at $HOST:$PORT"
fi

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

# Function to run server locally
run_local_server() {
    # Check if server is already running
    if check_local_server; then
        log "INFO" "Server is already running on port $PORT"
        return 0
    fi
    
    log "INFO" "Starting server on local host at $HOST:$PORT"
    
    # Check if the enhanced server script exists
    if [[ ! -f "examples/enhanced_hardware_server.py" ]]; then
        log "ERROR" "Enhanced hardware server script not found: examples/enhanced_hardware_server.py"
        exit 1
    fi
    
    # Start the server
    nohup python3 examples/enhanced_hardware_server.py --host "$HOST" --port "$PORT" > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > server.pid
    
    log "INFO" "Server started with PID $SERVER_PID, logs in $SERVER_LOG"
    
    # Wait for server to start (with timeout)
    log "INFO" "Waiting for server to become ready..."
    TIMEOUT=10
    for ((i=1; i<=TIMEOUT; i++)); do
        if check_local_server; then
            log "INFO" "Server is ready"
            return 0
        fi
        sleep 1
    done
    
    log "ERROR" "Server failed to start within $TIMEOUT seconds"
    if [[ -f "$SERVER_LOG" ]]; then
        log "ERROR" "Server log:"
        cat "$SERVER_LOG" | while read -r line; do
            log "ERROR" "  $line"
        done
    fi
    
    return 1
}

# Function to run server on remote host
run_remote_server() {
    # Create remote directory if it doesn't exist
    log "INFO" "Creating remote directory: $REMOTE_DIR"
    ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"
    
    # Copy server and client scripts to remote host
    log "INFO" "Copying server script to remote host"
    scp "examples/enhanced_hardware_server.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
    
    log "INFO" "Copying client script to remote host"
    scp "examples/enhanced_hardware_client.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
    
    # If audio file is specified, copy it to remote host
    if [[ -n "$AUDIO_FILE" && -f "$AUDIO_FILE" ]]; then
        log "INFO" "Copying audio file to remote host: $AUDIO_FILE"
        scp "$AUDIO_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
        # Update AUDIO_FILE to use the remote path
        AUDIO_FILE="$REMOTE_DIR/$(basename "$AUDIO_FILE")"
    fi
    
    # Ensure port is free on remote host
    log "INFO" "Ensuring port $PORT is free on remote host"
    ssh "$REMOTE_USER@$REMOTE_HOST" "lsof -ti:$PORT | xargs kill -9 2>/dev/null || true"
    
    # Create a simple startup script on the remote host
    log "INFO" "Creating startup script on remote host"
    cat > /tmp/start_server.sh << EOF
#!/bin/bash
cd $REMOTE_DIR
# Use nohup to ensure the server keeps running even if the SSH session ends
nohup python3 enhanced_hardware_server.py --host '$HOST' --port '$PORT' > server.log 2>&1 &
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
    scp /tmp/start_server.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
    ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_DIR/start_server.sh"
    
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
    if check_remote_server; then
        log "INFO" "Server is listening on port $PORT"
    else
        log "ERROR" "Server is not listening on port $PORT"
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
    
    return 0
}

# Function to execute command locally
execute_local_command() {
    log "INFO" "Executing command '$COMMAND' locally..."
    
    # Build the command line arguments
    CMD_ARGS="--host 127.0.0.1 --port $PORT --command $COMMAND"
    
    # Add command-specific arguments
    case "$COMMAND" in
        gpio)
            if [[ -z "$PIN" || -z "$STATE" ]]; then
                log "ERROR" "GPIO command requires --pin and --state"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --pin $PIN --state $STATE"
            ;;
        i2c)
            if [[ -z "$ADDRESS" || -z "$REGISTER" ]]; then
                log "ERROR" "I2C command requires --address and --register"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --address $ADDRESS --register $REGISTER"
            if [[ -n "$VALUE" ]]; then
                CMD_ARGS="$CMD_ARGS --value $VALUE"
            fi
            ;;
        lcd)
            if [[ "$CLEAR" == "true" ]]; then
                CMD_ARGS="$CMD_ARGS --clear"
            else
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "LCD command requires --text or --clear"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\" --line $LINE"
            fi
            ;;
        speaker)
            if [[ -z "$SUB_ACTION" ]]; then
                log "ERROR" "Speaker command requires --sub-action"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --sub-action $SUB_ACTION"
            
            if [[ "$SUB_ACTION" == "play_file" ]]; then
                if [[ -z "$AUDIO_FILE" ]]; then
                    log "ERROR" "play_file sub-action requires --audio-file"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --audio-file \"$AUDIO_FILE\""
            elif [[ "$SUB_ACTION" == "speak" ]]; then
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "speak sub-action requires --text"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\""
            fi
            ;;
        led_matrix)
            if [[ -z "$LED_ACTION" ]]; then
                log "ERROR" "LED matrix command requires --led-action"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --led-action $LED_ACTION"
            
            if [[ "$LED_ACTION" == "text" ]]; then
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "text LED action requires --text"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\""
                if [[ -n "$X" ]]; then
                    CMD_ARGS="$CMD_ARGS --x $X"
                fi
                if [[ -n "$Y" ]]; then
                    CMD_ARGS="$CMD_ARGS --y $Y"
                fi
            elif [[ "$LED_ACTION" == "pixel" ]]; then
                if [[ -z "$X" || -z "$Y" ]]; then
                    log "ERROR" "pixel LED action requires --x and --y"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --x $X --y $Y"
            fi
            ;;
    esac
    
    # Run the command
    log "INFO" "Running command: python3 examples/enhanced_hardware_client.py $CMD_ARGS"
    python3 examples/enhanced_hardware_client.py $CMD_ARGS > "$CLIENT_LOG" 2>&1
    EXIT_CODE=$?
    
    # Display the command output
    log "INFO" "Command output:"
    cat "$CLIENT_LOG" | while read -r line; do
        log "COMMAND" "  $line"
    done
    
    return $EXIT_CODE
}

# Function to execute command on remote host
execute_remote_command() {
    log "INFO" "Executing command '$COMMAND' on remote host..."
    
    # Build the command line arguments
    CMD_ARGS="--host 127.0.0.1 --port $PORT --command $COMMAND"
    
    # Add command-specific arguments
    case "$COMMAND" in
        gpio)
            if [[ -z "$PIN" || -z "$STATE" ]]; then
                log "ERROR" "GPIO command requires --pin and --state"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --pin $PIN --state $STATE"
            ;;
        i2c)
            if [[ -z "$ADDRESS" || -z "$REGISTER" ]]; then
                log "ERROR" "I2C command requires --address and --register"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --address $ADDRESS --register $REGISTER"
            if [[ -n "$VALUE" ]]; then
                CMD_ARGS="$CMD_ARGS --value $VALUE"
            fi
            ;;
        lcd)
            if [[ "$CLEAR" == "true" ]]; then
                CMD_ARGS="$CMD_ARGS --clear"
            else
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "LCD command requires --text or --clear"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\" --line $LINE"
            fi
            ;;
        speaker)
            if [[ -z "$SUB_ACTION" ]]; then
                log "ERROR" "Speaker command requires --sub-action"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --sub-action $SUB_ACTION"
            
            if [[ "$SUB_ACTION" == "play_file" ]]; then
                if [[ -z "$AUDIO_FILE" ]]; then
                    log "ERROR" "play_file sub-action requires --audio-file"
                    exit 1
                fi
                # AUDIO_FILE was already copied and path updated in run_remote_server
                CMD_ARGS="$CMD_ARGS --audio-file \"$AUDIO_FILE\""
            elif [[ "$SUB_ACTION" == "speak" ]]; then
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "speak sub-action requires --text"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\""
            fi
            ;;
        led_matrix)
            if [[ -z "$LED_ACTION" ]]; then
                log "ERROR" "LED matrix command requires --led-action"
                exit 1
            fi
            CMD_ARGS="$CMD_ARGS --led-action $LED_ACTION"
            
            if [[ "$LED_ACTION" == "text" ]]; then
                if [[ -z "$TEXT" ]]; then
                    log "ERROR" "text LED action requires --text"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --text \"$TEXT\""
                if [[ -n "$X" ]]; then
                    CMD_ARGS="$CMD_ARGS --x $X"
                fi
                if [[ -n "$Y" ]]; then
                    CMD_ARGS="$CMD_ARGS --y $Y"
                fi
            elif [[ "$LED_ACTION" == "pixel" ]]; then
                if [[ -z "$X" || -z "$Y" ]]; then
                    log "ERROR" "pixel LED action requires --x and --y"
                    exit 1
                fi
                CMD_ARGS="$CMD_ARGS --x $X --y $Y"
            fi
            ;;
    esac
    
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
    
    # Run the command with retry mechanism
    MAX_RETRIES=3
    for ((retry=1; retry<=MAX_RETRIES; retry++)); do
        log "INFO" "Running command: python3 enhanced_hardware_client.py $CMD_ARGS"
        CMD_OUTPUT=$(ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && python3 enhanced_hardware_client.py $CMD_ARGS" 2>&1)
        CMD_EXIT_CODE=$?
        
        if [[ $CMD_EXIT_CODE -eq 0 ]]; then
            log "SUCCESS" "Command executed successfully"
            echo "$CMD_OUTPUT" | while read -r line; do
                log "COMMAND" "  $line"
            done
            break
        else
            log "WARNING" "Attempt $retry/$MAX_RETRIES: Command failed (exit code: $CMD_EXIT_CODE)"
            
            if [[ $retry -eq $MAX_RETRIES ]]; then
                log "ERROR" "All attempts to execute command failed"
                log "ERROR" "Last output: $CMD_OUTPUT"
                
                # Check server logs for any issues
                REMOTE_ERROR_LOGS=$(ssh "$REMOTE_USER@$REMOTE_HOST" "if [[ -f '$REMOTE_DIR/server.log' ]]; then tail -n 20 '$REMOTE_DIR/server.log'; fi")
                if [[ ! -z "$REMOTE_ERROR_LOGS" ]]; then
                    log "ERROR" "Recent server logs:"
                    echo "$REMOTE_ERROR_LOGS" | while read -r line; do
                        log "ERROR" "  $line"
                    done
                fi
                return 1
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
    
    return 0
}

# Function to stop local server
stop_local_server() {
    if [[ -f "server.pid" ]]; then
        SERVER_PID=$(cat server.pid)
        log "INFO" "Stopping server on local host (PID $SERVER_PID)"
        kill -15 $SERVER_PID 2>/dev/null || true
        rm -f server.pid
    fi
}

# Function to stop remote server
stop_remote_server() {
    if [[ -n "$REMOTE_SERVER_PID" ]]; then
        log "INFO" "Stopping server on remote host (PID $REMOTE_SERVER_PID)"
        ssh "$REMOTE_USER@$REMOTE_HOST" "kill -15 $REMOTE_SERVER_PID 2>/dev/null || true"
    fi
}

# Main execution
if [[ "$LOCAL_MODE" == true ]]; then
    # Local mode
    run_local_server
    execute_local_command
    COMMAND_EXIT_CODE=$?
    stop_local_server
else
    # Remote mode
    run_remote_server
    execute_remote_command
    COMMAND_EXIT_CODE=$?
    stop_remote_server
fi

if [[ $COMMAND_EXIT_CODE -eq 0 ]]; then
    log "INFO" "Remote hardware operation completed successfully"
else
    log "ERROR" "Remote hardware operation failed (exit code: $COMMAND_EXIT_CODE)"
fi

log "INFO" "Script completed"
exit $COMMAND_EXIT_CODE
