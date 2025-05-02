#!/bin/bash
set -e

# Load .env from parent directory
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

if [ -z "$RPI_USERNAME" ] || [ -z "$RPI_HOST" ]; then
    echo "RPI_USERNAME or RPI_HOST not set in .env"
    exit 1
fi

REMOTE="$RPI_USERNAME@$RPI_HOST"
REMOTE_PATH="/home/$RPI_USERNAME"
#
#echo "[rpi_control] Syncing project files to $REMOTE:$REMOTE_PATH ..."
#rsync -avz \
#  --exclude 'venv' \
#  --exclude '.git' \
#  --exclude '__pycache__' \
#  --exclude '.tox' \
#  --exclude 'dist' \
#  --exclude 'build' \
#  --exclude '*.egg-info' \
#  --exclude '*.pyc' \
#  --exclude '*.pyo' \
#  --exclude '*.log' \
#  --exclude '*.sqlite3' \
#  --exclude '*.db' \
#  --exclude 'node_modules' \
#  --exclude '*.swp' \
#  --exclude '.mypy_cache' \
#  --exclude '.pytest_cache' \
#  --exclude '.idea' \
#  --exclude '.vscode' \
#  --exclude '.DS_Store' \
#  --exclude '*.bak' \
#  --exclude '*/.ipynb_checkpoints' \
#  ../../ "$REMOTE:$REMOTE_PATH"

echo "[rpi_control] Installing dependencies on remote using the Raspberry Pi specific installation script..."
ssh $REMOTE bash -c "'
set -e
cd $REMOTE_PATH/rpi_control
df -h
du -h --max-depth=1
sudo apt-get update && sudo apt-get install -y python3-pip python3-dev python3-rpi.gpio ffmpeg
if [ ! -d \"venv\" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip

# Use the Raspberry Pi specific installation script
bash install_rpi.sh

echo \"[rpi_control] Remote installation complete. To use, run: source venv/bin/activate\"
'"

echo "[rpi_control] Remote update and install complete."
