# Instalacja i konfiguracja środowiska

## Zarządzanie zależnościami z Conda

Projekt UnitApi/mcp używa Conda do zarządzania zależnościami, co zapewnia spójne środowisko na różnych platformach, w tym na Raspberry Pi.

### Dlaczego Conda?

- **Wieloplatformowość** - działa na Windows, Linux, macOS oraz na architekturze ARM (Raspberry Pi)
- **Zarządzanie pakietami binarnymi** - obsługuje zarówno pakiety Pythona, jak i zależności binarne
- **Izolowane środowiska** - eliminuje konflikty zależności między projektami
- **Powtarzalność** - zapewnia identyczne środowisko na wszystkich maszynach

### Instalacja środowiska

#### Automatyczna instalacja

1. **Linux/macOS**:
   ```bash
   chmod +x setup_environment.sh
   ./setup_environment.sh
   ```

2. **Windows**:
   ```
   setup_environment.bat
   ```

#### Ręczna instalacja

1. **Zainstaluj Conda**:
   - Dla systemów x86_64: [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
   - Dla Raspberry Pi: [Miniforge](https://github.com/conda-forge/miniforge)

2. **Utwórz środowisko**:
   ```bash
   conda env create -f environment.yml
   ```

3. **Aktywuj środowisko**:
   ```bash
   conda activate unitmcp
   ```

### Aktualizacja zależności

Jeśli zależności projektu zostały zaktualizowane, możesz zaktualizować swoje środowisko:

```bash
conda env update -f environment.yml
```

### Rozwiązywanie problemów

#### Konflikty zależności

Jeśli napotkasz konflikty zależności, spróbuj:

1. Usunąć środowisko i utworzyć je ponownie:
   ```bash
   conda remove -n unitmcp --all
   conda env create -f environment.yml
   ```

2. Jeśli problem dotyczy konkretnego pakietu, możesz zainstalować go ręcznie:
   ```bash
   conda activate unitmcp
   pip install <nazwa_pakietu>==<wersja>
   ```

#### Problemy specyficzne dla Raspberry Pi

Dla Raspberry Pi niektóre pakiety mogą wymagać kompilacji. W takim przypadku:

```bash
sudo apt-get install -y build-essential libatlas-base-dev
conda activate unitmcp
pip install <problematyczny_pakiet> --no-binary :all:
```

### Przejście z requirements.txt

Projekt wcześniej używał `requirements.txt`. Jeśli nadal chcesz korzystać z tego podejścia:

```bash
pip install -r requirements.txt
```

Jednak zalecamy przejście na system Conda, aby uniknąć problemów z zależnościami.
