#!/bin/bash
# install.sh: Install dependencies for rpi_control on remote Raspberry Pi
set -e

# Step 0: Upgrade pip to latest version
echo "[rpi_control] Upgrading pip to latest version..."
python3 -m pip install --upgrade pip || pip install --upgrade pip

echo "[rpi_control] Installing system packages..."
# System dependencies
sudo apt-get update && sudo apt-get install -y python3-pip python3-dev python3-rpi.gpio libasound2-dev

# Python venv setup
echo "[rpi_control] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
  echo "[rpi_control] Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate venv and install Python dependencies
echo "[rpi_control] Activating virtual environment and installing Python dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[rpi_control] Installation complete. To use, run: source venv/bin/activate"
