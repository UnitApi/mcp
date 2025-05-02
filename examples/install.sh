#!/bin/bash
# Instalacja środowiska TTS MCP + Ollama + unitmcp
set -e

# Tworzenie venv (jeśli nie istnieje)
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate

# Aktualizacja pip
pip install --upgrade pip

# Instalacja unitmcp (jeśli jest wymagany)
pip install -e ../../../  # zakładając, że jesteś w examples/tts i unitmcp jest repozytorium wyżej

# Instalacja wymaganych bibliotek
pip install pyttsx3 aiohttp requests paramiko

# Informacja o Ollama
cat << EOF

UWAGA:
Aby użyć klienta Ollama, musisz mieć uruchomiony lokalny serwer Ollama (np. tinyllama).
Więcej: https://ollama.com/

EOF

echo "\nŚrodowisko gotowe. Aktywuj venv: source venv/bin/activate"
echo "Uruchom: python tts_server.py"
