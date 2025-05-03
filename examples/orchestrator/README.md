# UnitMCP Orchestrator

Moduł Orchestrator służy do zarządzania przykładami w katalogu `examples` oraz do uruchamiania i monitorowania serwerów UnitMCP w sposób interaktywny.

## Instalacja

Moduł jest częścią pakietu UnitMCP i nie wymaga dodatkowej instalacji. Upewnij się, że masz zainstalowane wszystkie zależności:

```bash
pip install -r requirements.txt
```

## Uruchamianie

Orchestrator można uruchomić na kilka sposobów:

### 1. Z linii poleceń

```bash
python -m unitmcp.orchestrator.main
```

Dostępne opcje:
```
--examples-dir PATH     Ścieżka do katalogu z przykładami
--config-file PATH      Ścieżka do pliku konfiguracyjnego
--log-level LEVEL       Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
--verbose               Włącza szczegółowe logowanie
--no-shell              Nie uruchamia interaktywnego shella
--run EXAMPLE           Uruchamia przykład
--simulation BOOL       Uruchamia w trybie symulacji
--host HOST             Host do połączenia
--port PORT             Port do użycia
--ssh-username USER     Nazwa użytkownika SSH
--ssh-key-path PATH     Ścieżka do klucza SSH
--ssl BOOL              Włącza SSL
```

### 2. Z poziomu kodu Python

```python
from unitmcp.orchestrator import Orchestrator, OrchestratorShell

# Utworzenie instancji Orchestrator
orchestrator = Orchestrator()

# Uruchomienie interaktywnego shella
shell = OrchestratorShell(orchestrator)
shell.cmdloop()
```

### 3. Uruchomienie przykładu bez interaktywnego shella

```bash
python -m unitmcp.orchestrator.main --run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
```

## Dostępne komendy w interaktywnym shellu

Po uruchomieniu interaktywnego shella, dostępne są następujące komendy:

### Przeglądanie przykładów

- `list` - wyświetla wszystkie dostępne przykłady
- `list recent` - wyświetla ostatnio używane przykłady
- `list favorite` - wyświetla ulubione przykłady
- `list running` - wyświetla aktualnie uruchomione przykłady

### Zarządzanie przykładami

- `info <nazwa_przykładu>` - wyświetla szczegółowe informacje o przykładzie
- `select <nazwa_przykładu>` - wybiera przykład jako aktualnie używany
- `favorite <nazwa_przykładu>` - dodaje lub usuwa przykład z ulubionych

### Uruchamianie przykładów

- `run [nazwa_przykładu] [opcje]` - uruchamia przykład
  - `--simulation=<true|false>` - tryb symulacji (domyślnie: true)
  - `--host=<host>` - host do połączenia (domyślnie: localhost)
  - `--port=<port>` - port do użycia (domyślnie: 8080)
  - `--ssh-username=<username>` - nazwa użytkownika SSH (domyślnie: pi)
  - `--ssh-key-path=<path>` - ścieżka do klucza SSH (domyślnie: ~/.ssh/id_rsa)
  - `--ssl=<true|false>` - włącza SSL (domyślnie: false)

### Monitorowanie uruchomionych przykładów

- `status [id_runnera]` - sprawdza status uruchomionego przykładu
- `stop [id_runnera]` - zatrzymuje uruchomiony przykład
- `runners` - wyświetla wszystkie aktywne runnery

### Zarządzanie serwerami

- `connect <host> <port> [--ssl]` - łączy się z serwerem
- `disconnect` - rozłącza się z aktualnym serwerem
- `servers` - wyświetla listę ostatnio używanych serwerów

### Zarządzanie konfiguracją

- `env [nazwa_przykładu] [opcje]` - tworzy lub aktualizuje plik .env dla przykładu
  - opcje są takie same jak dla komendy `run`

### Inne komendy

- `refresh` - odświeża listę przykładów
- `help [komenda]` - wyświetla pomoc dla komendy
- `exit` lub `quit` - wychodzi z shella

## Przykłady użycia

### 1. Podstawowe uruchomienie Orchestratora

```bash
# Uruchomienie z minimalistycznym interfejsem
python -m unitmcp.orchestrator.main

# Uruchomienie z pełnym logowaniem
python -m unitmcp.orchestrator.main --verbose
```

### 2. Uruchomienie przykładu w trybie symulacji

```
mcp> run basic
```

### 3. Uruchomienie przykładu na fizycznym Raspberry Pi

```
mcp> run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
```

### 4. Uruchomienie przykładu z linii poleceń bez interaktywnego shella

```bash
python -m unitmcp.orchestrator.main --run basic --no-shell
```

### 5. Sprawdzenie statusu uruchomionego przykładu

```
mcp> status 12345678-1234-5678-1234-567812345678
```

### 6. Połączenie z serwerem

```
mcp> connect 192.168.1.100 8080
```

### 7. Zarządzanie ulubionymi przykładami

```
mcp> favorite basic
mcp> list favorite
```

### 8. Tworzenie pliku .env dla przykładu

```
mcp> env rpi_control --host=192.168.1.100 --port=8080
```

### 9. Uruchomienie przykładu z niestandardowym katalogiem przykładów

```bash
python -m unitmcp.orchestrator.main --examples-dir /path/to/examples
```

### 10. Uruchomienie przykładu z niestandardowym plikiem konfiguracyjnym

```bash
python -m unitmcp.orchestrator.main --config-file /path/to/config.json
```

## Programistyczne użycie modułu Orchestrator

### 1. Podstawowe użycie

```python
from unitmcp.orchestrator import Orchestrator

# Utworzenie instancji Orchestrator
orchestrator = Orchestrator()

# Pobranie listy dostępnych przykładów
examples = orchestrator.get_examples()
print(examples)

# Uruchomienie przykładu
runner_info = orchestrator.run_example(
    "rpi_control",
    simulation=False,
    host="192.168.1.100",
    ssh_username="pi"
)

# Sprawdzenie statusu
status = orchestrator.get_runner_status(runner_info["id"])
print(status)

# Zatrzymanie przykładu
orchestrator.stop_runner(runner_info["id"])
```

### 2. Zarządzanie przykładami

```python
from unitmcp.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Pobranie informacji o przykładzie
example_info = orchestrator.get_example("basic")
print(example_info)

# Dodanie przykładu do ulubionych
orchestrator.add_to_favorites("basic")

# Pobranie listy ulubionych przykładów
favorites = orchestrator.get_favorite_examples()
print(favorites)

# Pobranie listy ostatnio używanych przykładów
recent = orchestrator.get_recent_examples()
print(recent)
```

### 3. Zarządzanie serwerami

```python
from unitmcp.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Połączenie z serwerem
connection_info = orchestrator.connect_to_server(
    host="192.168.1.100",
    port=8080,
    ssl_enabled=False
)
print(connection_info)

# Pobranie listy ostatnio używanych serwerów
servers = orchestrator.get_recent_servers()
print(servers)

# Rozłączenie z serwerem
orchestrator.disconnect_from_server()
```

### 4. Tworzenie pliku .env dla przykładu

```python
from unitmcp.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Tworzenie pliku .env dla przykładu
env_file = orchestrator.create_env_file(
    example_name="rpi_control",
    simulation=False,
    host="192.168.1.100",
    port=8080
)
print(f"Utworzono plik .env: {env_file}")
```

### 5. Niestandardowa konfiguracja Orchestratora

```python
from unitmcp.orchestrator import Orchestrator

# Utworzenie instancji Orchestrator z niestandardowymi parametrami
orchestrator = Orchestrator(
    examples_dir="/path/to/examples",
    config_file="/path/to/config.json",
    quiet=True  # Minimalizuje ilość logów
)

# Zapisanie konfiguracji
orchestrator.save_config()
```

## Rozszerzanie funkcjonalności

Moduł Orchestrator można rozszerzać, dodając nowe funkcje do klas:
- `Orchestrator` - główna klasa zarządzająca
- `OrchestratorShell` - interaktywny shell

### Dodawanie nowej komendy do shella

```python
from unitmcp.orchestrator import OrchestratorShell

class CustomShell(OrchestratorShell):
    def do_custom_command(self, arg):
        """
        Opis nowej komendy.
        
        Usage: custom_command [opcje]
        """
        print(f"Wykonuję niestandardową komendę z argumentami: {arg}")
        # Implementacja komendy
        
# Użycie niestandardowego shella
from unitmcp.orchestrator import Orchestrator

orchestrator = Orchestrator()
shell = CustomShell(orchestrator)
shell.cmdloop()
```

### Rozszerzanie klasy Orchestrator

```python
from unitmcp.orchestrator import Orchestrator

class CustomOrchestrator(Orchestrator):
    def custom_method(self, param1, param2):
        """Niestandardowa metoda."""
        # Implementacja metody
        return {"result": "success", "param1": param1, "param2": param2}
        
# Użycie niestandardowego Orchestratora
orchestrator = CustomOrchestrator()
result = orchestrator.custom_method("value1", "value2")
print(result)
```

## Konfiguracja

Orchestrator używa pliku konfiguracyjnego `~/.unitmcp/orchestrator.json`, który zawiera:
- Domyślne ustawienia symulacji
- Konfigurację SSH
- Konfigurację SSL
- Listę ostatnio używanych przykładów
- Listę ulubionych przykładów
- Listę ostatnio używanych serwerów

### Przykładowy plik konfiguracyjny

```json
{
  "default_settings": {
    "simulation": true,
    "host": "localhost",
    "port": 8080,
    "ssl_enabled": false
  },
  "ssh_config": {
    "username": "pi",
    "key_path": "~/.ssh/id_rsa"
  },
  "recent_examples": [
    "basic",
    "rpi_control"
  ],
  "favorite_examples": [
    "basic"
  ],
  "recent_servers": [
    {
      "host": "192.168.1.100",
      "port": 8080,
      "ssl_enabled": false
    }
  ]
}
```

## Rozwiązywanie problemów

### Problem: Nie można znaleźć katalogu z przykładami

Upewnij się, że katalog `examples` istnieje w głównym katalogu projektu lub podaj pełną ścieżkę do katalogu z przykładami za pomocą opcji `--examples-dir`.

```bash
python -m unitmcp.orchestrator.main --examples-dir /path/to/examples
```

### Problem: Błędy importu modułów

Upewnij się, że pakiet UnitMCP jest zainstalowany w trybie rozwojowym:

```bash
pip install -e .
```

### Problem: Nie można połączyć się z serwerem

Sprawdź, czy serwer jest uruchomiony i dostępny:

```bash
ping <host>
```

Sprawdź, czy port jest otwarty:

```bash
telnet <host> <port>
```

### Problem: Błędy podczas uruchamiania przykładów

Włącz tryb verbose, aby zobaczyć więcej informacji o błędach:

```bash
python -m unitmcp.orchestrator.main --verbose
```

## Dobre praktyki

1. **Organizacja przykładów**: Każdy przykład powinien być w osobnym katalogu z plikiem README.md opisującym jego działanie.

2. **Pliki konfiguracyjne**: Używaj plików .env.example jako szablonów dla plików .env.

3. **Logowanie**: Używaj odpowiednich poziomów logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL).

4. **Obsługa błędów**: Zawsze obsługuj wyjątki i zwracaj informacje o błędach.

5. **Dokumentacja**: Dodawaj docstringi do wszystkich klas i metod.

## Przyszłe rozszerzenia

- Wsparcie dla kontenerów Docker
- Integracja z systemami CI/CD
- Interfejs webowy dla Orchestratora
- Automatyczne wykrywanie urządzeń w sieci
- Wsparcie dla wielu równoległych sesji
