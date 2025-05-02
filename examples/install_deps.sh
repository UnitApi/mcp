#!/bin/bash

# Skrypt instaluje wymagane zależności systemowe i pip
# Obsługuje Fedora, Ubuntu, Debian

set -e

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

install_fedora() {
    echo "Instaluję python3-devel (Fedora) ..."
    sudo dnf install -y python3-devel
}

install_debian() {
    echo "Instaluję python${PYTHON_VERSION}-dev (Debian/Ubuntu) ..."
    sudo apt-get update
    sudo apt-get install -y python${PYTHON_VERSION}-dev
}

if [ -f /etc/fedora-release ]; then
    echo "Wykryto Fedorę. Instalacja zależności..."
    install_fedora
elif [ -f /etc/debian_version ]; then
    echo "Wykryto Debiana/Ubuntu. Instalacja zależności..."
    install_debian
else
    echo "Nieznany system. Zainstaluj ręcznie python3-devel lub python3.x-dev."
fi

echo "Instalacja zależności pip..."
pip install -r requirements.txt

echo "Gotowe!"
