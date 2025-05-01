#!/bin/bash

# Fedora PyAudio Preparation Script

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check and install dependencies
prepare_system() {
    echo -e "${YELLOW}Preparing system for PyAudio installation...${NC}"

    # Check and install development tools and libraries
    echo -e "${YELLOW}Checking and installing required packages...${NC}"
    sudo dnf groupinstall -y "Development Tools"
    sudo dnf install -y \
        python3-devel \
        portaudio-devel \
        python3-pip \
        gcc \
        redhat-rpm-config

    # Upgrade pip and setuptools
    echo -e "${YELLOW}Upgrading pip and setuptools...${NC}"
    python3 -m pip install --upgrade pip setuptools wheel
}

# Function to verify PyAudio dependencies
verify_dependencies() {
    echo -e "${YELLOW}Verifying PyAudio dependencies...${NC}"

    # Check for portaudio library
    if ldconfig -p | grep -q libportaudio; then
        echo -e "${GREEN}PortAudio library found ✓${NC}"
    else
        echo -e "${RED}PortAudio library not found ✗${NC}"
        return 1
    }

    # Check Python development headers
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_INCLUDE_PATH="/usr/include/python${PYTHON_VERSION}"

    if [ -d "$PYTHON_INCLUDE_PATH" ]; then
        echo -e "${GREEN}Python ${PYTHON_VERSION} development headers found ✓${NC}"
    else
        echo -e "${RED}Python development headers not found ✗${NC}"
        return 1
    fi
}

# Main script
main() {
    echo -e "${GREEN}Fedora PyAudio Preparation Script${NC}"

    # Prepare system
    prepare_system

    # Verify dependencies
    if verify_dependencies; then
        echo -e "${GREEN}System is ready for PyAudio installation!${NC}"
        exit 0
    else
        echo -e "${RED}Some dependencies are missing. Please review the output above.${NC}"
        exit 1
    fi
}

# Run the main function
main