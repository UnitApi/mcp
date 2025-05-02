#!/bin/bash

# Common shell functions for MCP install scripts

create_venv() {
    local venv_dir=${1:-venv}
    if [ -d "$venv_dir" ]; then
        echo "Removing existing venv at $venv_dir..."
        rm -rf "$venv_dir"
    fi
    echo "Creating venv at $venv_dir..."
    python3 -m venv "$venv_dir"
    source "$venv_dir/bin/activate"
}

upgrade_pip() {
    echo "Upgrading pip..."
    pip install --upgrade pip
}

install_requirements() {
    local req_file=${1:-requirements.txt}
    if [ -f "$req_file" ]; then
        echo "Installing Python dependencies from $req_file..."
        pip install -r "$req_file"
    else
        echo "Requirements file $req_file not found!"
    fi
}

install_system_deps_dnf() {
    echo "Installing system dependencies via dnf..."
    sudo dnf update -y
    sudo dnf install -y \
        python3 python3-pip python3-devel python3-virtualenv \
        ffmpeg v4l-utils portaudio-devel opencv-devel alsa-lib-devel \
        libX11-devel libffi-devel openssl-devel gcc gcc-c++ make pkgconfig git redhat-rpm-config
}

install_tkinter_dnf() {
    echo "Installing tkinter via dnf..."
    sudo dnf install -y python3-tkinter
}

# Usage example in scripts:
# source "$(dirname "$0")/common.sh"
# create_venv venv
# upgrade_pip
# install_requirements requirements.txt
# install_system_deps_dnf
