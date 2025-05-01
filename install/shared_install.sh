#!/bin/bash
# Wspólne funkcje do instalacji środowiska dla różnych systemów

set -e

# Tworzenie i aktywacja venv
create_and_activate_venv() {
  VENV_PATH="$1"
  PYTHON_BIN=${2:-python3}
  if [ ! -d "$VENV_PATH" ]; then
    $PYTHON_BIN -m venv "$VENV_PATH"
  fi
  source "$VENV_PATH/bin/activate"
}

# Instalacja zależności pip
install_pip_requirements() {
  REQ_FILE="$1"
  pip install --upgrade pip
  pip install -r "$REQ_FILE"
}

# Instalacja dev dependencies
install_dev_requirements() {
  DEV_REQ_FILE="$1"
  if [ -f "$DEV_REQ_FILE" ]; then
    pip install -r "$DEV_REQ_FILE"
  fi
}

# Testowanie
run_tests() {
  if command -v pytest &> /dev/null; then
    pytest || echo "pytest failed"
  fi
  if command -v tox &> /dev/null; then
    tox || echo "tox failed"
  fi
}

# Instalacja zależności systemowych
default_system_deps_ubuntu=(python3 python3-pip python3-dev python3-venv ffmpeg v4l-utils portaudio19-dev libopencv-dev libasound2-dev libxlib-dev libffi-dev libssl-dev build-essential pkg-config git)
default_system_deps_fedora=(python3 python3-pip python3-devel python3-venv ffmpeg v4l-utils portaudio-devel opencv opencv-devel alsa-lib-devel libX11-devel libffi-devel openssl-devel gcc gcc-c++ make git)
default_system_deps_macos=(python3 portaudio ffmpeg opencv)

install_system_deps() {
  local os="$1"
  shift
  local pkgs=("$@")
  case "$os" in
    ubuntu)
      sudo apt-get update
      sudo apt-get install -y "${pkgs[@]}"
      ;;
    fedora)
      sudo dnf install -y "${pkgs[@]}"
      ;;
    macos)
      brew update
      brew install "${pkgs[@]}"
      ;;
    *)
      echo "Unknown OS: $os"
      ;;
  esac
}
