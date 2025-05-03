# UnitMCP Orchestrator

Moduł Orchestrator służy do zarządzania przykładami w katalogu `examples` oraz do uruchamiania i monitorowania serwerów UnitMCP w sposób interaktywny.

## Instalacja

Moduł jest częścią pakietu UnitMCP i nie wymaga dodatkowej instalacji.

## Uruchamianie

Orchestrator można uruchomić na kilka sposobów:

### 1. Z linii poleceń

```bash
python -m unitmcp.orchestrator.main
```

### 2. Z poziomu kodu Python

```python
from unitmcp import Orchestrator, OrchestratorShell

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

### Uruchomienie przykładu w trybie symulacji

```
orchestrator> run basic
```

### Uruchomienie przykładu na fizycznym Raspberry Pi

```
orchestrator> run rpi_control --simulation=false --host=192.168.1.100 --ssh-username=pi
```

### Sprawdzenie statusu uruchomionego przykładu

```
orchestrator> status 12345678-1234-5678-1234-567812345678
```

### Połączenie z serwerem

```
orchestrator> connect 192.168.1.100 8080
```

## Programistyczne użycie modułu Orchestrator

```python
from unitmcp import Orchestrator

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

## Rozszerzanie funkcjonalności

Moduł Orchestrator można rozszerzać, dodając nowe funkcje do klas:
- `Orchestrator` - główna klasa zarządzająca
- `OrchestratorShell` - interaktywny shell
- `ExampleManager` - zarządzanie przykładami
- `RunnerManager` - zarządzanie uruchomionymi instancjami

## Konfiguracja

Orchestrator używa pliku konfiguracyjnego `~/.unitmcp/orchestrator.json`, który zawiera:
- Domyślne ustawienia symulacji
- Konfigurację SSH
- Konfigurację SSL
- Listę ostatnio używanych przykładów
- Listę ulubionych przykładów
- Listę ostatnio używanych serwerów
