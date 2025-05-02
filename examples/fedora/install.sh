#!/bin/bash

# Installation script for Fedora/RHEL systems
set -e

echo "Installing unitmcp on Fedora/RHEL"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if a package is installed
is_installed() {
    rpm -q "$1" &> /dev/null
}

# System dependencies
echo "Installing system dependencies..."
sudo dnf update -y
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    python3-virtualenv \
    ffmpeg \
    v4l-utils \
    portaudio-devel \
    opencv-devel \
    alsa-lib-devel \
    libX11-devel \
    libffi-devel \
    openssl-devel \
    gcc \
    gcc-c++ \
    make \
    pkgconfig \
    git \
    redhat-rpm-config

# Optional: Install CUDA dependencies if NVIDIA GPU is present
if lspci | grep -i nvidia &> /dev/null; then
    echo "NVIDIA GPU detected, installing CUDA dependencies..."
    if ! is_installed cuda-toolkit; then
        sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/fedora/x86_64/cuda-fedora.repo
        sudo dnf install -y cuda-toolkit
    fi
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "${PROJECT_DIR}/.venv"
source "${PROJECT_DIR}/.venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
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
sudo "${SCRIPT_DIR}/configure_hardware.sh" list

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

# SELinux configuration if enabled
if command -v sestatus >/dev/null 2>&1 && sestatus | grep -q "SELinux status:\s*enabled"; then
    echo "Configuring SELinux policies..."
    sudo setsebool -P httpd_can_network_connect 1
    sudo setsebool -P domain_can_mmap_files 1
fi

echo "Installation complete!"
echo
echo "To activate the virtual environment, run:"
echo "source ${PROJECT_DIR}/.venv/bin/activate"
echo
echo "To configure specific hardware devices, use:"
echo "sudo ${SCRIPT_DIR}/configure_hardware.sh [video|audio|picamera|usb-audio] [device]"
