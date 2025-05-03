#!/bin/bash
# Skrypt do konfiguracji środowiska Conda dla projektu UnitApi/mcp

# Sprawdzenie, czy Conda jest zainstalowana
if ! command -v conda &> /dev/null; then
    echo "Conda nie jest zainstalowana. Instaluję Miniconda..."
    
    # Wykryj architekturę systemu
    ARCH=$(uname -m)
    
    if [ "$ARCH" == "x86_64" ]; then
        # Instalacja dla x86_64
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    elif [ "$ARCH" == "aarch64" ] || [ "$ARCH" == "armv7l" ]; then
        # Instalacja dla ARM (Raspberry Pi)
        wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh -O miniconda.sh
    else
        echo "Nieobsługiwana architektura: $ARCH"
        exit 1
    fi
    
    # Instalacja Miniconda
    bash miniconda.sh -b -p $HOME/miniconda
    rm miniconda.sh
    
    # Dodanie conda do PATH
    export PATH="$HOME/miniconda/bin:$PATH"
    
    # Inicjalizacja conda dla basha
    conda init bash
    
    echo "Zainstalowano Conda. Uruchom ponownie terminal lub wykonaj 'source ~/.bashrc'"
    echo "Następnie uruchom ten skrypt ponownie."
    exit 0
fi

# Tworzenie środowiska Conda z pliku environment.yml
echo "Tworzenie środowiska Conda z pliku environment.yml..."
conda env create -f environment.yml

# Aktywacja środowiska
echo "Aktywacja środowiska unitmcp..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate unitmcp

# Sprawdzenie, czy środowisko zostało poprawnie aktywowane
if [ $? -ne 0 ]; then
    echo "Nie udało się aktywować środowiska. Spróbuj ręcznie wykonać 'conda activate unitmcp'"
    exit 1
fi

echo "Środowisko zostało pomyślnie skonfigurowane!"
echo "Aby aktywować środowisko w przyszłości, użyj komendy: conda activate unitmcp"
echo "Aby uruchomić testy, użyj: python -m pytest tests/unitmcp/events/test_event_system.py -v"
