#!/bin/bash

# Installation script for macOS systems
set -e

echo "Installing unitmcp on macOS"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if Homebrew is installed
check_brew() {
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Installing now..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
}

# Function to check if a package is installed via Homebrew
is_installed() {
    brew list "$1" &> /dev/null
}

# Check and install Homebrew
check_brew

# Install Xcode Command Line Tools if not installed
if ! xcode-select -p &> /dev/null; then
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo "Please wait for Xcode Command Line Tools to finish installing, then press Enter"
    read -r
fi

# System dependencies
echo "Installing system dependencies..."
brew update

# Install Python if not present
if ! is_installed python@3.11; then
    brew install python@3.11
fi

# Install other dependencies
brew install \
    ffmpeg \
    opencv \
    portaudio \
    pkg-config \
    git

# Optional: Install CUDA dependencies if NVIDIA GPU is present
# Note: macOS typically uses Metal instead of CUDA
if system_profiler SPDisplaysDataType | grep -i nvidia &> /dev/null; then
    echo "NVIDIA GPU detected, but macOS typically uses Metal for GPU acceleration"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "${PROJECT_DIR}/.venv"
source "${PROJECT_DIR}/.venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
export LDFLAGS="-L/usr/local/opt/portaudio/lib"
export CPPFLAGS="-I/usr/local/opt/portaudio/include"
export PKG_CONFIG_PATH="/usr/local/opt/portaudio/lib/pkgconfig"

pip install -r "${PROJECT_DIR}/requirements.txt"

# Install development dependencies if present
if [ -f "${PROJECT_DIR}/requirements-dev.txt" ]; then
    echo "Installing development dependencies..."
    pip install -r "${PROJECT_DIR}/requirements-dev.txt"
fi

# Install the package in development mode
echo "Installing unitmcp package..."
pip install -e "${PROJECT_DIR}"

# Configure hardware
echo "Configuring hardware..."
"${SCRIPT_DIR}/configure_hardware.sh" list

# Install models if needed
if [ -f "${SCRIPT_DIR}/install_models.sh" ]; then
    echo "Installing AI models..."
    "${SCRIPT_DIR}/install_models.sh"
fi

# Setup service if needed
if [ -f "${SCRIPT_DIR}/setup_service.sh" ]; then
    echo "Setting up system service..."
    sudo "${SCRIPT_DIR}/setup_service.sh"
fi

# Configure audio permissions
echo "Configuring audio permissions..."
if ! groups | grep -q "audio"; then
    sudo dseditgroup -o create audio
    sudo dseditgroup -o edit -a "$(whoami)" -t user audio
fi

# Configure camera permissions
echo "Please grant camera access when prompted..."
tccutil reset Camera
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"

echo "Please grant microphone access when prompted..."
tccutil reset Microphone
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"

echo "Installation complete!"
echo
echo "To activate the virtual environment, run:"
echo "source ${PROJECT_DIR}/.venv/bin/activate"
echo
echo "Important Notes:"
echo "1. Make sure to grant camera and microphone permissions in System Preferences"
echo "2. You may need to restart your terminal for audio group changes to take effect"
echo
echo "To configure specific hardware devices, use:"
echo "${SCRIPT_DIR}/configure_hardware.sh [video|audio|usb-audio] [device]"
