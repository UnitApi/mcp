#!/usr/bin/env python3
if [ -d venv ]; then
    echo "[1/3] Usuwam stare środowisko venv..."
    rm -rf venv
fi

python3.11 -m venv venv
source venv/bin/activate

echo "[2/3] Aktualizacja pip"
pip install --upgrade pip

echo "[3/3] Instalacja zależności z requirements.txt"
pip install -r requirements.txt

echo "Gotowe! Środowisko działa na Pythonie 3.11."
