#!/bin/bash
# Script to install tkinter for different platforms

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux system"
    
    # Check for apt (Debian/Ubuntu)
    if command -v apt-get &> /dev/null; then
        echo "Installing tkinter using apt..."
        sudo apt-get update
        sudo apt-get install -y python3-tk python3-dev
    
    # Check for dnf (Fedora)
    elif command -v dnf &> /dev/null; then
        echo "Installing tkinter using dnf..."
        sudo dnf install -y python3-tkinter
    
    # Check for pacman (Arch)
    elif command -v pacman &> /dev/null; then
        echo "Installing tkinter using pacman..."
        sudo pacman -S tk
    
    # Check for zypper (openSUSE)
    elif command -v zypper &> /dev/null; then
        echo "Installing tkinter using zypper..."
        sudo zypper install -y python3-tk
    
    else
        echo "Could not determine package manager. Please install tkinter manually."
        echo "For Debian/Ubuntu: sudo apt-get install python3-tk python3-dev"
        echo "For Fedora: sudo dnf install python3-tkinter"
        echo "For Arch: sudo pacman -S tk"
        echo "For openSUSE: sudo zypper install python3-tk"
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    echo "Tkinter should be included with Python on macOS."
    echo "If you're experiencing issues, you can try reinstalling Python using Homebrew:"
    echo "brew install python"
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "You have Homebrew installed. You can use it to install/reinstall Python:"
        echo "brew install python"
    else
        echo "Consider installing Homebrew (https://brew.sh/) for easier package management."
    fi

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Detected Windows system"
    echo "Tkinter should be included with Python on Windows."
    echo "If you're experiencing issues, please reinstall Python from python.org"
    echo "and make sure to check the 'tcl/tk and IDLE' option during installation."

else
    echo "Unknown operating system: $OSTYPE"
    echo "Please install tkinter manually for your system."
fi

# Install other dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Installation complete!"
echo "If you encounter any issues with tkinter, please refer to the documentation."
