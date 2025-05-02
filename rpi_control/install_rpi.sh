#!/bin/bash
# Script to install unitmcp and mcp on Raspberry Pi without problematic dependencies

set -e  # Exit on error

echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y libasound2-dev ffmpeg  # Required for simpleaudio and pydub

# Remove mcp from requirements.txt temporarily to avoid the error
sed -i.bak '/^mcp$/d' requirements.txt

echo "Installing Python dependencies from requirements.txt..."
python -m pip install -r requirements.txt --upgrade

echo "Installing local unitmcp package without dependencies..."
cd ..
python -m pip install --no-deps -e .
cd rpi_control

echo "Installing local mcp package from python-sdk..."
cd ../python-sdk
if [ -d "python-sdk" ]; then
    cd python-sdk  # In case we're already in the parent directory
fi
python -m pip install --no-deps -e .
cd ../rpi_control

# Restore the original requirements.txt
mv requirements.txt.bak requirements.txt 2>/dev/null || true

echo "Installation completed successfully!"
echo "You can now run the examples with: python examples/hello_world.py"
