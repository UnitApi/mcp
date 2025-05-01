#!/bin/bash

# Comprehensive SpaCy Installation Script for Linux Distributions
# Supports: Ubuntu/Debian, Fedora, CentOS/RHEL, Arch Linux, OpenSUSE
# Updated to handle Python 3.13+ compatibility issues with legacy C extensions

# Exit on any error
set -e

# Logging
INSTALL_LOG="/tmp/spacy_install_$(date +%Y%m%d_%H%M%S).log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default spaCy version
SPACY_VERSION=""

# Default language models to install
MODELS=("en_core_web_sm")

# Default Python command
PYTHON_CMD="python3"

# Path to virtual environment
VENV_PATH=""

# Error handling function
handle_error() {
    echo -e "${RED}Error occurred during installation. Check log at $INSTALL_LOG for details.${NC}"
    exit 1
}

# Trap any errors and call error handling function
trap handle_error ERR

# Print usage information
usage() {
    echo -e "${BLUE}Usage: $0 [options]${NC}"
    echo -e "Options:"
    echo -e "  -h, --help              Show this help message"
    echo -e "  -v, --version VERSION   Install specific spaCy version (e.g., 3.6.1)"
    echo -e "  -m, --models \"MODEL1 MODEL2...\"  Space-separated list of models to install (default: en_core_web_sm)"
    echo -e "  -p, --python PATH       Path to Python executable (default: python3)"
    echo -e "  --venv PATH             Create and use a virtual environment at this path"
    echo -e "  --force-cython          Force Cython pre-installation (for older distros)"
    echo -e "  --no-verify             Skip verification step"
    echo -e "  --binary                Try binary installation first (default)"
    echo -e "  --no-binary             Force source installation"
    exit 0
}

# Parse command line arguments
parse_args() {
    FORCE_CYTHON=0
    SKIP_VERIFY=0
    USE_BINARY=1

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                ;;
            -v|--version)
                SPACY_VERSION="$2"
                shift 2
                ;;
            -m|--models)
                # Convert space-separated string to array
                IFS=' ' read -r -a MODELS <<< "$2"
                shift 2
                ;;
            -p|--python)
                PYTHON_CMD="$2"
                shift 2
                ;;
            --venv)
                VENV_PATH="$2"
                shift 2
                ;;
            --force-cython)
                FORCE_CYTHON=1
                shift
                ;;
            --no-verify)
                SKIP_VERIFY=1
                shift
                ;;
            --binary)
                USE_BINARY=1
                shift
                ;;
            --no-binary)
                USE_BINARY=0
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                usage
                ;;
        esac
    done
}

# Check if running as root/sudo
check_permissions() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}Warning: Running without sudo or root permissions.${NC}"
        echo -e "${YELLOW}This may work for user-local installation but might fail for system dependencies.${NC}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Installation cancelled.${NC}"
            exit 1
        fi
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif command -v lsb_release &> /dev/null; then
        lsb_release -i | cut -d: -f2 | sed s/'^\t'//
    else
        echo "unknown"
    fi
}

# Check Python version compatibility
check_python_version() {
    echo -e "${YELLOW}Checking Python version...${NC}"

    # Get Python version
    local python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local python_full_version=$($PYTHON_CMD -c "import sys; print(sys.version.split()[0])")

    echo -e "Detected Python version: ${BLUE}$python_full_version${NC}"

    # Convert version to integers for comparison
    local major_version=$(echo $python_version | cut -d. -f1)
    local minor_version=$(echo $python_version | cut -d. -f2)

    if [[ $major_version -eq 3 && $minor_version -ge 13 ]]; then
        echo -e "${YELLOW}Python 3.13+ detected. Modern versions of spaCy have compatibility issues with Python 3.13+.${NC}"
        echo -e "${YELLOW}Will try to install an older compatible version or use prebuild wheels.${NC}"

        if [[ -z "$SPACY_VERSION" ]]; then
            # For Python 3.13+, use 3.5.3 which is more compatible
            SPACY_VERSION="3.5.3"
            echo -e "${YELLOW}Setting spaCy version to $SPACY_VERSION for compatibility${NC}"
        fi

        # Check if specific version was requested
        if [[ $USE_BINARY -eq 1 ]]; then
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install spacy==$SPACY_VERSION"
        else
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install --no-binary spacy spacy==$SPACY_VERSION"
        fi
    elif [[ $major_version -eq 3 && $minor_version -ge 7 && $minor_version -le 12 ]]; then
        echo -e "${GREEN}Python version is compatible with modern spaCy.${NC}"
        if [[ -z "$SPACY_VERSION" ]]; then
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install spacy"
        else
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install spacy==$SPACY_VERSION"
        fi
    elif [[ $major_version -eq 3 && $minor_version -lt 7 ]]; then
        echo -e "${YELLOW}Python 3.6 or lower detected. Using spaCy 3.0.x series.${NC}"
        if [[ -z "$SPACY_VERSION" ]]; then
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install 'spacy<3.1.0'"
        else
            SPACY_INSTALL_CMD="$PYTHON_CMD -m pip install spacy==$SPACY_VERSION"
        fi
    else
        echo -e "${RED}Unsupported Python version. spaCy requires Python 3.6+${NC}"
        exit 1
    fi

    echo -e "Will use install command: ${BLUE}$SPACY_INSTALL_CMD${NC}"

    # Return the installation command
    echo "$SPACY_INSTALL_CMD"
}

# Setup virtual environment if requested
setup_venv() {
    if [[ -n "$VENV_PATH" ]]; then
        echo -e "${YELLOW}Setting up virtual environment at $VENV_PATH...${NC}"

        # Check if venv module is available
        if ! $PYTHON_CMD -c "import venv" &> /dev/null; then
            echo -e "${RED}Python venv module not available. Please install it first.${NC}"
            exit 1
        fi

        # Create virtual environment if it doesn't exist
        if [ ! -d "$VENV_PATH" ]; then
            $PYTHON_CMD -m venv "$VENV_PATH"
        fi

        # Activate virtual environment
        if [ -f "$VENV_PATH/bin/activate" ]; then
            echo -e "${GREEN}Activating virtual environment...${NC}"
            source "$VENV_PATH/bin/activate"
            PYTHON_CMD="python"  # In venv, just use 'python'
        else
            echo -e "${RED}Failed to create virtual environment.${NC}"
            exit 1
        fi
    fi
}

# Install dependencies based on distribution
install_dependencies() {
    local distro=$1

    echo -e "${YELLOW}Installing system dependencies...${NC}"

    case "$distro" in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                gcc \
                g++ \
                cmake \
                libpython3-dev \
                pkg-config
            ;;
        fedora)
            dnf install -y @development-tools || dnf5 install -y @development-tools
            dnf install -y \
                python3-pip \
                python3-devel \
                python3-virtualenv \
                gcc-c++ \
                cmake \
                python3-numpy \
                python3-setuptools \
                pkg-config \
                || dnf5 install -y \
                python3-pip \
                python3-devel \
                python3-virtualenv \
                gcc-c++ \
                cmake \
                python3-numpy \
                python3-setuptools \
                pkg-config
            ;;
        centos|rhel)
            yum groupinstall -y "Development Tools"
            yum install -y \
                python3-pip \
                python3-devel \
                python3-virtualenv \
                gcc-c++ \
                cmake \
                pkgconfig
            ;;
        arch)
            pacman -Syu --noconfirm
            pacman -S --noconfirm \
                python-pip \
                python-virtualenv \
                base-devel \
                cmake \
                pkgconf
            ;;
        opensuse*)
            zypper refresh
            zypper install -y \
                python3-pip \
                python3-devel \
                python3-virtualenv \
                gcc-c++ \
                cmake \
                pkg-config
            ;;
        *)
            echo -e "${YELLOW}Unsupported distribution: $distro${NC}"
            echo -e "${YELLOW}Installing minimum requirements with pip...${NC}"
            $PYTHON_CMD -m pip install --upgrade pip setuptools wheel
            ;;
    esac
}

# Upgrade pip and setuptools
upgrade_pip() {
    echo -e "${YELLOW}Upgrading pip and setuptools...${NC}"
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel

    # Install Cython if forced
    if [[ $FORCE_CYTHON -eq 1 ]]; then
        echo -e "${YELLOW}Installing/upgrading Cython (pre-requirement for spaCy)...${NC}"
        $PYTHON_CMD -m pip install --upgrade cython
    fi
}

# Try to use a prebuilt wheel if available for version 3.5.1 or similar
try_prebuilt_wheel() {
    echo -e "${YELLOW}Trying to find prebuilt wheel for spaCy...${NC}"

    # For Python 3.13, try to use one of the last versions that might have prebuilt wheels
    if [[ $USE_BINARY -eq 1 ]]; then
        for version in "3.5.3" "3.5.2" "3.5.1" "3.5.0" "3.4.0"; do
            echo -e "${YELLOW}Trying spaCy version $version...${NC}"
            if $PYTHON_CMD -m pip install --only-binary=:all: spacy==$version; then
                echo -e "${GREEN}Successfully installed prebuilt wheel for spaCy $version!${NC}"
                return 0
            fi
        done
    fi

    return 1
}

# Install SpaCy with language models
install_spacy() {
    local install_cmd=$1
    echo -e "${YELLOW}Installing spaCy...${NC}"

    # Try with prebuilt wheel first if Python is 3.13+
    if [[ $($PYTHON_CMD -c "import sys; print(sys.version_info.minor >= 13 and sys.version_info.major == 3)") == "True" ]]; then
        if try_prebuilt_wheel; then
            # Succeeded with prebuilt wheel
            true
        elif $install_cmd; then
            # Regular installation succeeded
            echo -e "${GREEN}Regular installation of spaCy succeeded!${NC}"
        else
            # Try pip download and direct install as a last resort
            echo -e "${YELLOW}Regular installation failed, trying legacy installation method...${NC}"

            # Create temp directory for the download
            local temp_dir=$(mktemp -d)
            echo -e "${YELLOW}Using temporary directory: $temp_dir${NC}"

            # Try smaller legacy version that may work
            LEGACY_VERSION="3.0.9"
            echo -e "${YELLOW}Trying to install legacy version $LEGACY_VERSION...${NC}"

            # Try to install it
            if $PYTHON_CMD -m pip install spacy==$LEGACY_VERSION; then
                echo -e "${GREEN}Successfully installed spaCy $LEGACY_VERSION!${NC}"
            else
                echo -e "${RED}All installation methods failed.${NC}"
                return 1
            fi
        fi
    else
        # Just try the regular installation for Python < 3.13
        if $install_cmd; then
            echo -e "${GREEN}spaCy installed successfully!${NC}"
        else
            echo -e "${RED}Installation failed.${NC}"
            return 1
        fi
    fi

    # Install language models
    echo -e "${YELLOW}Installing language models: ${MODELS[*]}${NC}"
    for model in "${MODELS[@]}"; do
        echo -e "${YELLOW}Installing $model...${NC}"
        if ! $PYTHON_CMD -m spacy download $model; then
            echo -e "${YELLOW}Direct download failed, trying pip installation for $model...${NC}"
            if ! $PYTHON_CMD -m pip install https://github.com/explosion/spacy-models/releases/download/${model/-/}/${model/-/_}-py3-none-any.whl; then
                echo -e "${YELLOW}Pip installation failed, skipping model $model.${NC}"
            fi
        fi
    done

    return 0
}

# Verify SpaCy installation
verify_installation() {
    if [[ $SKIP_VERIFY -eq 1 ]]; then
        echo -e "${YELLOW}Skipping verification as requested.${NC}"
        return 0
    fi

    echo -e "${YELLOW}Verifying SpaCy installation...${NC}"
    if $PYTHON_CMD -c "import spacy; print(f'SpaCy version: {spacy.__version__}')"; then
        echo -e "${GREEN}SpaCy verified successfully!${NC}"

        # Only run the test if any models were installed
        if [[ ${#MODELS[@]} -gt 0 ]]; then
            # Test with a simple example
            echo -e "${YELLOW}Testing with a simple example...${NC}"
            if $PYTHON_CMD -c "
import spacy
try:
    print('Loading model...')
    nlp = spacy.load('${MODELS[0]}')
    print('Processing text...')
    doc = nlp('This is a test sentence for SpaCy. It was installed successfully!')
    print('Tokens:', [token.text for token in doc])
    print('SpaCy is working correctly!')
except Exception as e:
    print(f'Error: {e}')
    print('Test without model...')
    # Try without model
    nlp = spacy.blank('en')
    doc = nlp('Testing blank model')
    print('Tokens:', [token.text for token in doc])
    print('SpaCy basic functionality works!')
"; then
                echo -e "${GREEN}SpaCy is working!${NC}"
            else
                echo -e "${RED}SpaCy test example failed.${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}No models specified, skipping model test.${NC}"
        fi
    else
        echo -e "${RED}SpaCy verification failed.${NC}"
        return 1
    fi
}

# Main installation process
main() {
    parse_args "$@"

    local distro=$(detect_distro)

    echo -e "${GREEN}SpaCy Installation Script${NC}"
    echo -e "${GREEN}=========================${NC}"
    echo -e "${GREEN}Detected Linux Distribution: ${distro}${NC}" | tee -a "$INSTALL_LOG"

    {
        echo "SpaCy Installation Log Started: $(date)"
        echo "Distribution: $distro"
        echo "Python command: $PYTHON_CMD"
        echo "SpaCy version: ${SPACY_VERSION:-latest}"
        echo "Models to install: ${MODELS[*]}"
        echo "------------------------------"
    } >> "$INSTALL_LOG"

    # Log each step
    check_permissions

    # Install system dependencies
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    install_dependencies "$distro" 2>&1 | tee -a "$INSTALL_LOG"

    # Setup virtual environment if requested
    if [[ -n "$VENV_PATH" ]]; then
        setup_venv 2>&1 | tee -a "$INSTALL_LOG"
    fi

    echo -e "${YELLOW}Upgrading pip...${NC}"
    upgrade_pip 2>&1 | tee -a "$INSTALL_LOG"

    # Check Python version and get install command
    local spacy_install_cmd=$(check_python_version 2>&1 | tee -a "$INSTALL_LOG")

    # Extract the actual command from output
    spacy_install_cmd=$(echo "$spacy_install_cmd" | grep "pip install" | tail -n 1)

    echo -e "${YELLOW}Installing SpaCy...${NC}"
    install_spacy "$spacy_install_cmd" 2>&1 | tee -a "$INSTALL_LOG"

    echo -e "${YELLOW}Verifying installation...${NC}"
    verify_installation 2>&1 | tee -a "$INSTALL_LOG"

    {
        echo "------------------------------"
        echo "SpaCy Installation Completed: $(date)"
    } >> "$INSTALL_LOG"

    echo -e "${GREEN}SpaCy installation completed successfully!${NC}"
    echo -e "${GREEN}Detailed log available at: $INSTALL_LOG${NC}"

    # Deactivate virtual environment if it was used
    if [[ -n "$VENV_PATH" ]]; then
        if type deactivate &>/dev/null; then
            deactivate
        fi
    fi
}

# Execute main function with all arguments
main "$@"

exit 0