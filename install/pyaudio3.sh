#!/bin/bash

# Homebrew Python PyAudio Preparation Script

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check and install dependencies
prepare_system() {
    echo -e "${YELLOW}Preparing system for PyAudio installation...${NC}"

    # Check and install system-level dependencies
    echo -e "${YELLOW}Checking and installing required packages...${NC}"

    # For Fedora
    if command -v dnf &> /dev/null; then
        sudo dnf install -y \
            portaudio-devel \
            redhat-rpm-config
    fi

    # For Homebrew Python
    echo -e "${YELLOW}Checking Homebrew Python configuration...${NC}"
    PYTHON_EXE=$(which python3.13)
    if [ -z "$PYTHON_EXE" ]; then
        echo -e "${RED}Homebrew Python 3.13 not found!${NC}"
        return 1
    fi

    # Verify PortAudio
    if ldconfig -p | grep -q libportaudio; then
        echo -e "${GREEN}PortAudio library found ✓${NC}"
    else
        echo -e "${RED}PortAudio library not found ✗${NC}"
        return 1
    fi
}

# Function to install system dependencies
install_build_dependencies() {
    echo -e "${YELLOW}Installing build dependencies...${NC}"

    # Fedora-specific build tools
    if command -v dnf &> /dev/null; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y \
            python3-devel \
            gcc \
            gcc-c++
    fi
}

# Main script
main() {
    echo -e "${GREEN}Homebrew Python PyAudio Preparation Script${NC}"

    # Prepare system
    if ! prepare_system; then
        echo -e "${RED}System preparation failed ✗${NC}"
        exit 1
    fi

    # Install build dependencies
    if ! install_build_dependencies; then
        echo -e "${RED}Build dependency installation failed ✗${NC}"
        exit 1
    fi

    echo -e "${GREEN}System is ready for PyAudio installation! ✓${NC}"
    exit 0
}

# Run the main function
main