#!/bin/bash
set -e

# System dependencies
sudo apt-get update && sudo apt-get install -y python3-pip python3-dev python3-rpi.gpio libasound2-dev

# Python venv setup
if [ ! -d "venv" ]; then
  echo "[rpi_control] Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate venv and install Python dependencies
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[rpi_control] Installation complete. To use, run: source venv/bin/activate"
