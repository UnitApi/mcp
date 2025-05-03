@echo off
:: Skrypt do konfiguracji środowiska Conda dla projektu UnitApi/mcp na Windows

:: Sprawdzenie, czy Conda jest zainstalowana
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Conda nie jest zainstalowana. Proszę zainstalować Miniconda ze strony:
    echo https://docs.conda.io/en/latest/miniconda.html
    echo Po instalacji uruchom ten skrypt ponownie.
    pause
    exit /b 1
)

:: Tworzenie środowiska Conda z pliku environment.yml
echo Tworzenie środowiska Conda z pliku environment.yml...
call conda env create -f environment.yml

:: Aktywacja środowiska
echo Aktywacja środowiska unitmcp...
call conda activate unitmcp

:: Sprawdzenie, czy środowisko zostało poprawnie aktywowane
if %ERRORLEVEL% neq 0 (
    echo Nie udało się aktywować środowiska. Spróbuj ręcznie wykonać 'conda activate unitmcp'
    pause
    exit /b 1
)

echo Środowisko zostało pomyślnie skonfigurowane!
echo Aby aktywować środowisko w przyszłości, użyj komendy: conda activate unitmcp
echo Aby uruchomić testy, użyj: python -m pytest tests/unitmcp/events/test_event_system.py -v
pause
