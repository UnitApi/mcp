#!/bin/bash
# Script to install unitmcp on Raspberry Pi without problematic dependencies

set -e  # Exit on error

echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y libasound2-dev ffmpeg  # Required for simpleaudio and pydub

echo "Installing Python dependencies from requirements.txt..."
python -m pip install -r requirements.txt

echo "Installing local unitmcp package without dependencies..."
cd ..
python -m pip install --no-deps -e .
cd rpi_control

echo "Installation completed successfully!"
echo "You can now run the examples with: python examples/hello_world.py"
