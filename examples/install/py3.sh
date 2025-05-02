#!/bin/bash

# Source common functions
source "$(dirname "$0")/common.sh"

# System dependencies (dnf/brew)
install_system_deps_dnf
install_tkinter_dnf

# Brew-specific
brew install python-tk
gcc_bin=$(which gcc)
brew install gcc@11
sudo ln -sf $gcc_bin /usr/local/bin/gcc-11
ls -la /usr/local/bin/gcc-11
export CC=gcc-11

# Python/Tkinter check
python -c "import sys; print(f'Python version: {sys.version}'); import tkinter; print(f'Tkinter version: {tkinter.TkVersion}')"

# Virtual environment
create_venv venv
upgrade_pip
install_requirements requirements.txt

which python3  # Upewnij się, że to /usr/bin/python3, nie /home/linuxbrew/...

# Testy
pytest
tox