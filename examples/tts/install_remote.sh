#!/bin/bash
# install_remote.sh - Remotely installs TTS server and dependencies and starts the server

# Default values
REMOTE_USER="$USER"
REMOTE_PATH="~/UnitApi/mcp-examples/tts"
PYTHON_CMD="python3"

# Help function
show_help() {
    echo "Usage: $0 <remote_host> [options]"
    echo ""
    echo "Arguments:"
    echo "  remote_host             Remote host address (IP or hostname)"
    echo ""
    echo "Options:"
    echo "  -u, --user USER         SSH username (default: current user)"
    echo "  -p, --path PATH         Remote path for TTS files (default: ~/UnitApi/mcp-examples/tts)"
    echo "  --python CMD            Python command on remote host (default: python3)"
    echo "  -h, --help              Show this help message"
    exit 1
}

# Parse arguments
if [ $# -lt 1 ]; then
    show_help
fi

REMOTE_HOST="$1"
shift

while [ $# -gt 0 ]; do
    case "$1" in
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -p|--path)
            REMOTE_PATH="$2"
            shift 2
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

echo "Installing TTS server on remote host: $REMOTE_HOST"
echo "User: $REMOTE_USER"
echo "Remote path: $REMOTE_PATH"
echo "Python command: $PYTHON_CMD"

# Create remote directory if it doesn't exist
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH"

# Copy TTS server files to remote host
echo "Copying TTS server files to remote host..."
scp tts_server.py "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
scp txt.env "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/" 2>/dev/null || echo "Warning: txt.env not copied"

# Install required packages on remote host
echo "Installing required packages on remote host..."
ssh "$REMOTE_USER@$REMOTE_HOST" "pip install pyttsx3 aiohttp"

# Create server.sh script on remote host
echo "Creating server.sh script on remote host..."
cat > /tmp/server.sh << EOF
#!/bin/bash
cd $REMOTE_PATH
$PYTHON_CMD tts_server.py
EOF

scp /tmp/server.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
ssh "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_PATH/server.sh"
rm /tmp/server.sh

# Start the TTS server on remote host
echo "Starting TTS server on remote host..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && nohup ./server.sh > tts_server.log 2>&1 &"

echo "TTS server installed and started on $REMOTE_HOST"
echo "Log file: $REMOTE_PATH/tts_server.log"
echo ""
echo "To connect to this remote TTS server, update the URL in your client script:"
echo "url = \"http://$REMOTE_HOST:8081/tts\""
