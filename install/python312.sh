#!/bin/bash
# Instalacja środowiska na Pythonie 3.12.x
# Skrypt wykrywa pyenv i korzysta z niego, jeśli jest dostępny,
# w przeciwnym razie próbuje użyć systemowego python3.12

set -e

PYTHON_VERSION=3.12.3
PROJECT_DIR="$(dirname "$(dirname "$0")")"
cd "$PROJECT_DIR"

# Sprawdź, czy pyenv jest dostępny
if command -v pyenv >/dev/null 2>&1; then
    echo "[1/6] Instalacja Pythona $PYTHON_VERSION przez pyenv (jeśli nie masz)"
    if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
        pyenv install "$PYTHON_VERSION"
    fi
    echo "[2/6] Ustawienie lokalnej wersji Pythona przez pyenv"
    pyenv local "$PYTHON_VERSION"
    PYTHON_BIN="python"
else
    echo "pyenv nie jest zainstalowany. Spróbuję użyć systemowego python3.12."
    if ! command -v python3.12 >/dev/null 2>&1; then
        echo "Brak python3.12 w systemie. Zainstaluj go ręcznie lub użyj pyenv."
        exit 1
    fi
    PYTHON_BIN="python3.12"
fi

if [ -d venv ]; then
    echo "[3/6] Usuwam stare środowisko venv..."
    rm -rf venv
fi

echo "[4/6] Tworzę nowe środowisko venv na Pythonie 3.12"
$PYTHON_BIN -m venv venv
source venv/bin/activate

echo "[5/6] Aktualizacja pip"
pip install --upgrade pip

echo "[6/6] Instalacja zależności z requirements.txt"
pip install -r requirements.txt

echo "Gotowe! Środowisko działa na Pythonie 3.12."
