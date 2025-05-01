#!/bin/bash

# Comprehensive PyAudio Installation Script

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect package manager and OS
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

# Install system-level dependencies
install_system_dependencies() {
    local pkg_manager=$1

    echo -e "${YELLOW}Installing system dependencies...${NC}"

    case $pkg_manager in
        apt)
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                portaudio19-dev \
                python3-dev \
                python3-pip \
                gcc
            ;;
        dnf)
            sudo dnf groupinstall -y "Development Tools"
            sudo dnf install -y \
                portaudio-devel \
                python3-devel \
                python3-pip \
                gcc
            ;;
        yum)
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                portaudio-devel \
                python3-devel \
                python3-pip \
                gcc
            ;;
        pacman)
            sudo pacman -Sy --noconfirm \
                base-devel \
                portaudio \
                python-pip \
                gcc
            ;;
        *)
            echo -e "${RED}Unsupported package manager. Please install dependencies manually.${NC}"
            exit 1
            ;;
    esac
}

# Install PyAudio with multiple methods
install_pyaudio() {
    echo -e "${YELLOW}Attempting to install PyAudio...${NC}"

    # Ensure pip and wheel are up to date
    pip3 install --upgrade pip wheel

    # Method 1: Standard installation
    pip3 install pyaudio && return 0

    # Method 2: No binary installation
    pip3 install --no-binary :all: pyaudio && return 0

    # Method 3: With specific compilation flags
    CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib" pip3 install pyaudio && return 0

    # Method 4: Alternate compilation approach
    python3 -m pip install --upgrade --force-reinstall --no-use-pep517 pyaudio && return 0

    # If all methods fail
    echo -e "${RED}Failed to install PyAudio${NC}"
    return 1
}

# Verify PyAudio installation
verify_pyaudio() {
    echo -e "${YELLOW}Verifying PyAudio installation...${NC}"

    python3 -c "
import sys
try:
    import pyaudio
    print('\n${GREEN}PyAudio installed successfully!${NC}')
    print(f'PyAudio version: {pyaudio.__version__}')
except ImportError as e:
    print(f'\n${RED}PyAudio import failed: {e}${NC}')
    sys.exit(1)
"
}

# Main installation script
main() {
    echo -e "${YELLOW}PyAudio Installation Troubleshooter${NC}"

    # Detect package manager
    PKG_MANAGER=$(detect_package_manager)

    if [ "$PKG_MANAGER" == "unknown" ]; then
        echo -e "${RED}Could not detect package manager. Manual intervention required.${NC}"
        exit 1
    fi

    # Install system dependencies
    install_system_dependencies "$PKG_MANAGER"

    # Install PyAudio
    if install_pyaudio; then
        # Verify installation
        verify_pyaudio
    else
        echo -e "${RED}PyAudio installation failed. Please check system dependencies.${NC}"
        exit 1
    fi
}

# Run the main function
main