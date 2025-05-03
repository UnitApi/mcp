@echo off
REM Skrypt uruchamiający UnitMCP z automatyczną instalacją pakietu

REM Przejdź do katalogu skryptu
cd /d "%~dp0"

REM Uruchom wrapper Pythona
python run.py %*
