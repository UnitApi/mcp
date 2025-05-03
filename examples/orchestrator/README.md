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
  ```
  mcp> list
  ```

- `list recent` - wyświetla ostatnio używane przykłady
  ```
  mcp> list recent
  ```

- `list favorite` - wyświetla ulubione przykłady
  ```
  mcp> list favorite
  ```

- `list running` - wyświetla aktualnie uruchomione przykłady
  ```
  mcp> list running
  ```

- `list with-runner` - wyświetla przykłady posiadające plik runner.py
  ```
  mcp> list with-runner
  ```

- `list with-server` - wyświetla przykłady posiadające plik server.py
  ```
  mcp> list with-server
  ```

### Zarządzanie przykładami

- `info <nazwa_przykładu>` - wyświetla szczegółowe informacje o przykładzie
  ```
  mcp> info basic
  ```

- `select <nazwa_przykładu>` - wybiera przykład jako aktualnie używany
  ```
  mcp> select rpi_control
  ```

- `favorite <nazwa_przykładu>` - dodaje lub usuwa przykład z ulubionych
  ```
  mcp> favorite basic
  ```

- `unfavorite <nazwa_przykładu>` - usuwa przykład z ulubionych
  ```
  mcp> unfavorite basic
  ```

- `readme <nazwa_przykładu>` - wyświetla zawartość pliku README.md dla przykładu
  ```
  mcp> readme basic
  ```

### Uruchamianie przykładów

- `run [nazwa_przykładu] [opcje]` - uruchamia przykład
  - `--simulation=<true|false>` - tryb symulacji (domyślnie: true)
  - `--host=<host>` - host do połączenia (domyślnie: localhost)
  - `--port=<port>` - port do użycia (domyślnie: 8080)
  - `--ssh-username=<username>` - nazwa użytkownika SSH (domyślnie: pi)
  - `--ssh-key-path=<path>` - ścieżka do klucza SSH (domyślnie: ~/.ssh/id_rsa)
  - `--ssl=<true|false>` - włącza SSL (domyślnie: false)
  - `--timeout=<seconds>` - maksymalny czas oczekiwania na uruchomienie (domyślnie: 30)
  - `--log-level=<level>` - poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `--env-file=<path>` - ścieżka do pliku .env do użycia

  ```
  # Uruchomienie przykładu w trybie symulacji
  mcp> run basic
  
  # Uruchomienie przykładu na fizycznym urządzeniu
  mcp> run rpi_control --simulation=false --host=192.168.1.100
  
  # Uruchomienie przykładu z niestandardowym portem i SSL
  mcp> run server --port=8443 --ssl=true
  
  # Uruchomienie przykładu z niestandardowym użytkownikiem SSH i kluczem
  mcp> run rpi_control --ssh-username=admin --ssh-key-path=~/.ssh/custom_key
  
  # Uruchomienie przykładu z niestandardowym poziomem logowania
  mcp> run basic --log-level=DEBUG
  
  # Uruchomienie przykładu z istniejącym plikiem .env
  mcp> run rpi_control --env-file=./custom.env
  ```

### Monitorowanie uruchomionych przykładów

- `status [id_runnera]` - sprawdza status uruchomionego przykładu
  ```
  # Sprawdzenie statusu konkretnego runnera
  mcp> status 12345678-1234-5678-1234-567812345678
  
  # Sprawdzenie statusu ostatnio uruchomionego runnera
  mcp> status
  ```

- `stop [id_runnera]` - zatrzymuje uruchomiony przykład
  ```
  # Zatrzymanie konkretnego runnera
  mcp> stop 12345678-1234-5678-1234-567812345678
  
  # Zatrzymanie ostatnio uruchomionego runnera
  mcp> stop
  ```

- `runners` - wyświetla wszystkie aktywne runnery
  ```
  mcp> runners
  ```

- `monitor [id_runnera]` - monitoruje status uruchomionego przykładu w czasie rzeczywistym
  ```
  # Monitorowanie konkretnego runnera
  mcp> monitor 12345678-1234-5678-1234-567812345678
  
  # Monitorowanie ostatnio uruchomionego runnera
  mcp> monitor
  ```

- `logs [id_runnera]` - wyświetla logi uruchomionego przykładu
  ```
  # Wyświetlenie logów konkretnego runnera
  mcp> logs 12345678-1234-5678-1234-567812345678
  
  # Wyświetlenie logów ostatnio uruchomionego runnera
  mcp> logs
  ```

### Zarządzanie serwerami

- `connect <host> <port> [--ssl]` - łączy się z serwerem
  ```
  # Połączenie z lokalnym serwerem
  mcp> connect localhost 8080
  
  # Połączenie z serwerem na Raspberry Pi
  mcp> connect 192.168.1.100 8080
  
  # Połączenie z serwerem używającym SSL
  mcp> connect 192.168.1.100 8443 --ssl
  
  # Połączenie z serwerem z timeoutem
  mcp> connect 192.168.1.100 8080 --timeout=10
  ```

- `disconnect` - rozłącza się z aktualnym serwerem
  ```
  mcp> disconnect
  ```

- `servers` - wyświetla listę ostatnio używanych serwerów
  ```
  mcp> servers
  ```

- `ping <host> [port]` - sprawdza dostępność serwera
  ```
  # Sprawdzenie dostępności serwera
  mcp> ping 192.168.1.100
  
  # Sprawdzenie dostępności serwera na konkretnym porcie
  mcp> ping 192.168.1.100 8080
  ```

- `devices` - wyświetla listę urządzeń podłączonych do aktualnego serwera
  ```
  mcp> devices
  ```

- `control <device_id> <command> [params]` - kontroluje urządzenie podłączone do serwera
  ```
  # Włączenie diody LED
  mcp> control led1 set_state on
  
  # Wyświetlenie tekstu na wyświetlaczu
  mcp> control display1 set_text "Hello World"
  
  # Ustawienie koloru diody RGB
  mcp> control rgb1 set_color 255 0 0
  ```

### Zarządzanie konfiguracją

- `env [nazwa_przykładu] [opcje]` - tworzy lub aktualizuje plik .env dla przykładu
  - opcje są takie same jak dla komendy `run`
  ```
  # Utworzenie pliku .env dla przykładu rpi_control
  mcp> env rpi_control --host=192.168.1.100 --port=8080
  
  # Utworzenie pliku .env z włączonym SSL
  mcp> env server --ssl=true --port=8443
  
  # Utworzenie pliku .env z niestandardowym użytkownikiem SSH
  mcp> env rpi_control --ssh-username=admin --ssh-key-path=~/.ssh/custom_key
  
  # Utworzenie pliku .env z wyłączonym trybem symulacji
  mcp> env hardware --simulation=false
  ```

- `config [get|set|reset] [klucz] [wartość]` - zarządza konfiguracją Orchestratora
  ```
  # Wyświetlenie całej konfiguracji
  mcp> config get
  
  # Wyświetlenie konkretnej wartości
  mcp> config get default_simulation
  
  # Ustawienie wartości
  mcp> config set default_port 8443
  
  # Resetowanie konfiguracji do wartości domyślnych
  mcp> config reset
  ```

- `save-config` - zapisuje aktualną konfigurację do pliku
  ```
  mcp> save-config
  ```

### Inne komendy

- `refresh` - odświeża listę przykładów
  ```
  mcp> refresh
  ```

- `help [komenda]` - wyświetla pomoc dla komendy
  ```
  # Wyświetlenie ogólnej pomocy
  mcp> help
  
  # Wyświetlenie pomocy dla konkretnej komendy
  mcp> help run
  ```

- `exit` lub `quit` - wychodzi z shella
  ```
  mcp> exit
  ```

- `clear` - czyści ekran
  ```
  mcp> clear
  ```

- `version` - wyświetla wersję Orchestratora
  ```
  mcp> version
  ```

- `batch <przykład1> <przykład2> ...` - uruchamia sekwencję przykładów
  ```
  # Uruchomienie sekwencji przykładów
  mcp> batch basic server rpi_control
  ```

- `export <nazwa_przykładu> <plik>` - eksportuje konfigurację przykładu do pliku
  ```
  # Eksport konfiguracji do pliku JSON
  mcp> export rpi_control config.json
  ```

- `import <plik>` - importuje konfigurację z pliku
  ```
  # Import konfiguracji z pliku JSON
  mcp> import config.json
  ```

## Przykłady użycia

### 1. Podstawowe uruchomienie Orchestratora

```bash
# Uruchomienie z minimalistycznym interfejsem
python -m unitmcp.orchestrator.main

# Uruchomienie z pełnym logowaniem
python -m unitmcp.orchestrator.main --verbose

# Uruchomienie z określonym poziomem logowania
python -m unitmcp.orchestrator.main --log-level=DEBUG

# Uruchomienie z niestandardowym katalogiem przykładów
python -m unitmcp.orchestrator.main --examples-dir /path/to/examples

# Uruchomienie z niestandardowym plikiem konfiguracyjnym
python -m unitmcp.orchestrator.main --config-file /path/to/config.json
```

### 2. Uruchamianie przykładów

```
# Uruchomienie przykładu w trybie symulacji
mcp> run basic

# Uruchomienie przykładu z określonymi parametrami
mcp> run basic --simulation=true --log-level=DEBUG

# Uruchomienie przykładu na fizycznym Raspberry Pi
mcp> run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi

# Uruchomienie przykładu z SSL
mcp> run server --ssl=true --port=8443

# Uruchomienie przykładu z niestandardowym timeoutem
mcp> run basic --timeout=60

# Uruchomienie przykładu z istniejącym plikiem .env
mcp> run rpi_control --env-file=./custom.env
```

### 3. Uruchamianie przykładów z linii poleceń

```bash
# Uruchomienie przykładu bez interaktywnego shella
python -m unitmcp.orchestrator.main --run basic --no-shell

# Uruchomienie przykładu z określonymi parametrami
python -m unitmcp.orchestrator.main --run rpi_control --simulation=false --host=192.168.1.100 --no-shell

# Uruchomienie przykładu z SSL
python -m unitmcp.orchestrator.main --run server --ssl=true --port=8443 --no-shell

# Uruchomienie przykładu z niestandardowym poziomem logowania
python -m unitmcp.orchestrator.main --run basic --log-level=DEBUG --no-shell
```

### 4. Monitorowanie uruchomionych przykładów

```
# Sprawdzenie statusu uruchomionego przykładu
mcp> status 12345678-1234-5678-1234-567812345678

# Sprawdzenie statusu ostatnio uruchomionego przykładu
mcp> status

# Monitorowanie uruchomionego przykładu w czasie rzeczywistym
mcp> monitor 12345678-1234-5678-1234-567812345678

# Wyświetlenie logów uruchomionego przykładu
mcp> logs 12345678-1234-5678-1234-567812345678

# Zatrzymanie uruchomionego przykładu
mcp> stop 12345678-1234-5678-1234-567812345678

# Wyświetlenie wszystkich aktywnych runnerów
mcp> runners
```

### 5. Zarządzanie serwerami

```
# Połączenie z lokalnym serwerem
mcp> connect localhost 8080

# Połączenie z serwerem na Raspberry Pi
mcp> connect 192.168.1.100 8080

# Połączenie z serwerem używającym SSL
mcp> connect 192.168.1.100 8443 --ssl

# Sprawdzenie dostępności serwera
mcp> ping 192.168.1.100

# Wyświetlenie listy urządzeń podłączonych do serwera
mcp> devices

# Kontrolowanie urządzenia podłączonego do serwera
mcp> control led1 set_state on

# Rozłączenie z serwerem
mcp> disconnect

# Wyświetlenie listy ostatnio używanych serwerów
mcp> servers
```

### 6. Zarządzanie przykładami

```
# Wyświetlenie listy wszystkich przykładów
mcp> list

# Wyświetlenie listy ostatnio używanych przykładów
mcp> list recent

# Wyświetlenie listy ulubionych przykładów
mcp> list favorite

# Wyświetlenie listy aktualnie uruchomionych przykładów
mcp> list running

# Wyświetlenie szczegółowych informacji o przykładzie
mcp> info basic

# Dodanie przykładu do ulubionych
mcp> favorite basic

# Usunięcie przykładu z ulubionych
mcp> unfavorite basic

# Wyświetlenie zawartości pliku README.md dla przykładu
mcp> readme basic
```

### 7. Zarządzanie konfiguracją

```
# Tworzenie pliku .env dla przykładu
mcp> env rpi_control --host=192.168.1.100 --port=8080

# Tworzenie pliku .env z włączonym SSL
mcp> env server --ssl=true --port=8443

# Wyświetlenie aktualnej konfiguracji
mcp> config get

# Ustawienie wartości w konfiguracji
mcp> config set default_port 8443

# Resetowanie konfiguracji do wartości domyślnych
mcp> config reset

# Zapisanie aktualnej konfiguracji do pliku
mcp> save-config
```

### 8. Operacje wsadowe i eksport/import

```
# Uruchomienie sekwencji przykładów
mcp> batch basic server rpi_control

# Eksport konfiguracji przykładu do pliku
mcp> export rpi_control config.json

# Import konfiguracji z pliku
mcp> import config.json
```

### 9. Uruchamianie niestandardowego shella

```bash
# Uruchomienie niestandardowego shella
python -m examples.orchestrator.custom_shell

# Uruchomienie niestandardowego shella z określonym poziomem logowania
python -m examples.orchestrator.custom_shell --log-level=DEBUG

# Uruchomienie niestandardowego shella z niestandardowym katalogiem przykładów
python -m examples.orchestrator.custom_shell --examples-dir /path/to/examples
```

### 10. Monitorowanie i kontrola urządzeń

```
# Połączenie z serwerem
mcp> connect 192.168.1.100 8080

# Wyświetlenie listy urządzeń
mcp> devices

# Włączenie diody LED
mcp> control led1 set_state on

# Wyświetlenie tekstu na wyświetlaczu
mcp> control display1 set_text "Hello World"

# Ustawienie koloru diody RGB
mcp> control rgb1 set_color 255 0 0

# Monitorowanie stanu przycisku
mcp> monitor button1
```

### 11. Uruchamianie przykładów z różnymi konfiguracjami

```
# Uruchomienie przykładu z domyślnymi ustawieniami
mcp> run basic

# Uruchomienie przykładu z niestandardowymi ustawieniami
mcp> run rpi_control --simulation=false --host=192.168.1.100 --port=8080 --ssh-username=pi --ssh-key-path=~/.ssh/id_rsa --ssl=false

# Uruchomienie przykładu z zapisaniem konfiguracji do pliku .env
mcp> env rpi_control --simulation=false --host=192.168.1.100
mcp> run rpi_control --env-file=./.env
```

### 12. Zarządzanie wieloma serwerami

```
# Połączenie z pierwszym serwerem
mcp> connect 192.168.1.100 8080
mcp> devices

# Rozłączenie i połączenie z drugim serwerem
mcp> disconnect
mcp> connect 192.168.1.101 8080
mcp> devices

# Wyświetlenie listy ostatnio używanych serwerów
mcp> servers

# Ponowne połączenie z pierwszym serwerem
mcp> connect 192.168.1.100 8080
```

### 13. Debugowanie i rozwiązywanie problemów

```
# Uruchomienie z pełnym logowaniem
python -m unitmcp.orchestrator.main --verbose

# Sprawdzenie statusu uruchomionego przykładu
mcp> status 12345678-1234-5678-1234-567812345678

# Wyświetlenie logów uruchomionego przykładu
mcp> logs 12345678-1234-5678-1234-567812345678

# Sprawdzenie dostępności serwera
mcp> ping 192.168.1.100

# Odświeżenie listy przykładów
mcp> refresh
```

### 14. Automatyzacja zadań

```
# Uruchomienie sekwencji przykładów
mcp> batch basic server rpi_control

# Uruchomienie przykładu z linii poleceń i zapisanie logów do pliku
python -m unitmcp.orchestrator.main --run basic --no-shell > logs.txt 2>&1

# Uruchomienie przykładu z timeoutem
mcp> run basic --timeout=30
```

### 15. Integracja z systemami CI/CD

```bash
# Uruchomienie przykładu w trybie nieinteraktywnym
python -m unitmcp.orchestrator.main --run basic --no-shell --log-level=ERROR

# Uruchomienie przykładu z określonymi parametrami
python -m unitmcp.orchestrator.main --run rpi_control --simulation=true --no-shell

# Uruchomienie przykładu i zapisanie wyniku do pliku
python -m unitmcp.orchestrator.main --run basic --no-shell > result.txt 2>&1
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
orchestrator.add_favorite_example("basic")

# Usunięcie przykładu z ulubionych
orchestrator.remove_favorite_example("basic")

# Pobranie listy ulubionych przykładów
favorites = orchestrator.get_favorite_examples()
print(favorites)

# Pobranie listy ostatnio używanych przykładów
recent = orchestrator.get_recent_examples()
print(recent)

# Odświeżenie listy przykładów
orchestrator._discover_examples()

# Sprawdzenie czy przykład istnieje
if "basic" in orchestrator.get_examples():
    print("Przykład 'basic' istnieje")

# Filtrowanie przykładów według typu
runner_examples = {name: info for name, info in orchestrator.get_examples().items() if info.get("has_runner")}
server_examples = {name: info for name, info in orchestrator.get_examples().items() if info.get("has_server")}
print(f"Przykłady z runner.py: {len(runner_examples)}")
print(f"Przykłady z server.py: {len(server_examples)}")
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
client = connection_info.get("client")
if client:
    client.disconnect()

# Sprawdzenie dostępności serwera
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = s.connect_ex(("192.168.1.100", 8080))
is_available = (result == 0)
s.close()
print(f"Server is available: {is_available}")

# Kontrolowanie urządzenia podłączonego do serwera
if connection_info.get("status") == "connected":
    client = connection_info.get("client")
    response = client.control_device("led1", {"state": "on"})
    print(response)

# Pobranie listy urządzeń podłączonych do serwera
if connection_info.get("status") == "connected":
    client = connection_info.get("client")
    devices = client.get_devices()
    print(devices)

# Monitorowanie stanu urządzenia
import time
if connection_info.get("status") == "connected":
    client = connection_info.get("client")
    for _ in range(5):  # Monitor for 5 seconds
        state = client.get_device_state("button1")
        print(f"Button state: {state}")
        time.sleep(1)
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

# Tworzenie pliku .env z włączonym SSL
env_file = orchestrator.create_env_file(
    example_name="server",
    ssl_enabled=True,
    port=8443
)
print(f"Utworzono plik .env z SSL: {env_file}")

# Tworzenie pliku .env z niestandardowym użytkownikiem SSH
env_file = orchestrator.create_env_file(
    example_name="rpi_control",
    ssh_username="admin",
    ssh_key_path="~/.ssh/custom_key"
)
print(f"Utworzono plik .env z niestandardowym użytkownikiem SSH: {env_file}")

# Sprawdzenie czy plik .env istnieje
import os
example = orchestrator.get_example("rpi_control")
env_path = os.path.join(example["path"], ".env")
if os.path.exists(env_path):
    print(f"Plik .env istnieje: {env_path}")
    
    # Odczytanie zawartości pliku .env
    with open(env_path, 'r') as f:
        env_content = f.read()
    print(f"Zawartość pliku .env:\n{env_content}")
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

# Ustawienie domyślnych wartości w konfiguracji
orchestrator.config["default_settings"] = {
    "simulation": False,
    "host": "192.168.1.100",
    "port": 8443,
    "ssl_enabled": True
}
orchestrator.save_config()

# Ustawienie konfiguracji SSH
orchestrator.config["ssh_config"] = {
    "default_username": "admin",
    "key_path": "~/.ssh/custom_key",
    "known_hosts_path": "~/.ssh/known_hosts"
}
orchestrator.save_config()

# Dodanie serwera do listy ostatnio używanych
if "recent_servers" not in orchestrator.config:
    orchestrator.config["recent_servers"] = []
    
server_info = "192.168.1.100:8443"
if server_info not in orchestrator.config["recent_servers"]:
    orchestrator.config["recent_servers"].insert(0, server_info)
    orchestrator.config["recent_servers"] = orchestrator.config["recent_servers"][:10]  # Keep only 10 most recent
    orchestrator.save_config()

# Odczytanie konfiguracji z pliku
import json
with open(orchestrator.config_file, 'r') as f:
    config_data = json.load(f)
print(f"Konfiguracja: {json.dumps(config_data, indent=2)}")
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
        
    def

```

## Konfiguracja niestandardowa

Orchestrator domyślnie korzysta z plików konfiguracyjnych znajdujących się w repozytorium, ale możliwe jest użycie własnych konfiguracji:

### Użycie niestandardowego pliku .env

Możesz określić własny plik .env podczas uruchamiania przykładu:

```bash
# Uruchomienie przykładu z własnym plikiem .env
mcp> run rpi_control --simulation=false --host=192.168.188.154 --ssh-username=pi --ssh-password=pi --port=9515 --env-file=~/.env
```

### Użycie niestandardowego katalogu konfiguracyjnego

Możesz utworzyć własny katalog konfiguracyjny i wskazać go podczas uruchamiania Orchestratora:

```bash
# Utworzenie własnego katalogu konfiguracyjnego
mkdir -p ~/my_unitmcp_configs/env
mkdir -p ~/my_unitmcp_configs/server

# Kopiowanie i dostosowanie domyślnych plików konfiguracyjnych
cp /path/to/unitmcp/configs/env/default.env ~/my_unitmcp_configs/env/custom.env
cp /path/to/unitmcp/examples/rpi_control/config/server.yaml ~/my_unitmcp_configs/server/

# Uruchomienie Orchestratora z własnym katalogiem konfiguracyjnym
python -m unitmcp.orchestrator.main --config-dir=~/my_unitmcp_configs
```

### Ustawienie zmiennej środowiskowej UNITMCP_CONFIG_PATH

Możesz ustawić zmienną środowiskową, aby wskazać niestandardowy katalog konfiguracyjny:

```bash
# Ustawienie zmiennej środowiskowej
export UNITMCP_CONFIG_PATH=~/my_unitmcp_configs

# Dodanie do .bashrc lub .zshrc dla trwałego efektu
echo 'export UNITMCP_CONFIG_PATH=~/my_unitmcp_configs' >> ~/.bashrc
```

## Rozwiązywanie problemów

### Problem z importem modułów

Jeśli napotykasz błędy importu modułów, upewnij się, że pakiet UnitMCP jest zainstalowany w trybie deweloperskim:

```bash
cd /path/to/unitmcp
pip install -e .
```

### Konflikt portów

Jeśli serwer nie może się uruchomić z powodu zajętego portu:

```
Error starting server: [Errno 98] error while attempting to bind on address ('127.0.0.1', 8000): [errno 98] address already in use
```

Rozwiązania:
1. Użyj innego portu: `--port=9515`
2. Znajdź i zakończ proces używający tego portu:
   ```bash
   sudo lsof -i :8000
   sudo kill <PID>
   ```

### Brak pliku konfiguracyjnego

Jeśli pojawia się błąd braku pliku konfiguracyjnego:

```
Error loading configuration from config/server.yaml: [Errno 2] No such file or directory: 'config/server.yaml'
```

Rozwiązania:
1. Utwórz brakujący plik konfiguracyjny:
   ```bash
   mkdir -p config
   cp /path/to/unitmcp/examples/rpi_control/config/server.yaml config/
   ```
2. Określ ścieżkę do istniejącego pliku konfiguracyjnego:
   ```bash
   mcp> run rpi_control --config=/path/to/existing/server.yaml
   ```

### Problemy z połączeniem SSH

Jeśli masz problemy z połączeniem SSH:

1. Upewnij się, że podałeś prawidłowe dane logowania:
   ```bash
   mcp> run rpi_control --ssh-username=pi --ssh-password=pi --ssh-port=22
   ```
2. Sprawdź, czy host jest dostępny:
   ```bash
   ping 192.168.188.154
   ```
3. Spróbuj połączyć się ręcznie przez SSH:
   ```bash
   ssh pi@192.168.188.154 -p 22
   ```

## Zaawansowane użycie

### Uruchamianie przykładów z parametrami specyficznymi dla przykładu

Niektóre przykłady mogą wymagać dodatkowych parametrów. Możesz je przekazać jako argumenty:

```bash
mcp> run rpi_control --simulation=false --host=192.168.188.154 --blink_duration=0.5 --loop_count=10
```

### Uruchamianie przykładów z niestandardowym plikiem konfiguracyjnym serwera

```bash
mcp> run rpi_control --config=/path/to/custom/server.yaml
```

### Łączenie wielu opcji konfiguracyjnych

```bash
mcp> run rpi_control --simulation=false --host=192.168.188.154 --ssh-username=pi --ssh-password=pi --port=9515 --env-file=~/.env --config=/path/to/custom/server.yaml --log-level=DEBUG
```
