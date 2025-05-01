#!/bin/bash

# Installation script for Ubuntu/Debian systems (deduplikowany)
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SHARED_INSTALL="$PROJECT_DIR/install/shared_install.sh"

if [ ! -f "$SHARED_INSTALL" ]; then
  echo "Brak pliku shared_install.sh! Przerwij."
  exit 1
fi
source "$SHARED_INSTALL"

# Instalacja zależności systemowych
install_system_deps ubuntu "${default_system_deps_ubuntu[@]}"

# Tworzenie i aktywacja venv
create_and_activate_venv "$PROJECT_DIR/.venv" python3

# Instalacja pip requirements
install_pip_requirements "$PROJECT_DIR/requirements.txt"

# Instalacja dev requirements jeśli istnieją
install_dev_requirements "$PROJECT_DIR/requirements-dev.txt"

# Instalacja CUDA dependencies jeśli NVIDIA GPU jest obecny
if lspci | grep -i nvidia &> /dev/null; then
    echo "NVIDIA GPU detected, installing CUDA dependencies..."
    if ! is_installed nvidia-cuda-toolkit; then
        sudo apt-get install -y nvidia-cuda-toolkit
    fi
fi

# Konfiguracja sprzętu
echo "Configuring hardware..."
sudo "${SCRIPT_DIR}/configure_hardware.sh" list

# Instalacja modeli jeśli potrzebne
if [ -f "${SCRIPT_DIR}/install_models.sh" ]; then
    echo "Installing AI models..."
    "${SCRIPT_DIR}/install_models.sh"
fi

# Ustawienie usługi jeśli potrzebne
if [ -f "${SCRIPT_DIR}/setup_service.sh" ]; then
    echo "Setting up system service..."
    sudo "${SCRIPT_DIR}/setup_service.sh"
fi

echo "Installation complete!"
echo
echo "To activate the virtual environment, run:"
echo "source ${PROJECT_DIR}/.venv/bin/activate"
echo
echo "To configure specific hardware devices, use:"
echo "sudo ${SCRIPT_DIR}/configure_hardware.sh [video|audio|picamera|usb-audio] [device]"
