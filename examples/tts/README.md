# Text-to-Speech (TTS) and Speech-to-Text (STT) Examples

Przykłady integracji MCP Hardware z syntezą mowy (Text-to-Speech), rozpoznawaniem mowy (Speech-to-Text) oraz zdalnym uruchamianiem serwera TTS/STT.

## Pliki
- `server.py` — Serwer MCP, który odbiera tekst i odtwarza go na głośniku komputera (pyttsx3, endpoint HTTP /tts).
- `get_weather_from_ollama.py` — Klient pobierający prognozę pogody z modelu Ollama i wysyłający ją do serwera TTS.
- `tts_server_runner.py` — Skrypt uruchamiający serwer TTS na zdalnym urządzeniu przez SSH (wymaga paramiko).
- `install_local.sh` — Skrypt instalujący serwer TTS lokalnie oraz Ollama.
- `install_remote.sh` — Skrypt instalujący serwer TTS na zdalnym urządzeniu przez SSH.
- `start_server.sh` — Skrypt uruchamiający serwer TTS lokalnie.
- `start_client.sh` — Skrypt uruchamiający klienta TTS lokalnie.
- `install_minimal_ollama.sh` — Skrypt instalujący minimalną konfigurację Ollama do testowania protokołu UnitMCP z funkcjami TTS i STT.
- `stt_server.py` — Serwer MCP, który nagrywa dźwięk z mikrofonu i konwertuje go na tekst (tworzony przez install_minimal_ollama.sh).
- `unitmcp_client.py` — Klient UnitMCP obsługujący zarówno TTS jak i STT (tworzony przez install_minimal_ollama.sh).

## Instalacja i uruchomienie

### Standardowa instalacja lokalna (tylko TTS)
```bash
./install_local.sh
```

### Standardowe uruchomienie lokalne (tylko TTS)
1. Uruchom serwer TTS:
   ```bash
   ./start_server.sh
   ```
2. Uruchom klienta (wymaga działającego serwera Ollama):
   ```bash
   ./start_client.sh
   ```

### Minimalna instalacja Ollama (TTS + STT)
Aby zainstalować minimalną konfigurację Ollama do testowania protokołu UnitMCP z funkcjami TTS i STT:
```bash
./install_minimal_ollama.sh
```

### Uruchomienie minimalnej konfiguracji (TTS + STT)
1. Uruchom serwer Ollama (jeśli nie jest już uruchomiony):
   ```bash
   ./start_ollama.sh
   ```
2. Uruchom serwer TTS:
   ```bash
   ./start_tts_server.sh
   ```
3. Uruchom serwer STT:
   ```bash
   ./start_stt_server.sh
   ```
4. Uruchom klienta UnitMCP:
   ```bash
   ./start_unitmcp_client.sh
   ```

Klient UnitMCP obsługuje różne tryby działania:
- Pełna demonstracja: `./start_unitmcp_client.sh --mode full-loop`
- Tylko TTS: `./start_unitmcp_client.sh --mode tts --text "Hello world"`
- Tylko STT: `./start_unitmcp_client.sh --mode stt --duration 5`
- STT do Ollama: `./start_unitmcp_client.sh --mode stt-ollama --duration 5`
- Prognoza pogody do TTS: `./start_unitmcp_client.sh --mode weather-tts`

Szczegółowe informacje na temat minimalnej konfiguracji Ollama znajdują się w pliku [README_MINIMAL_OLLAMA.md](README_MINIMAL_OLLAMA.md).

### Instalacja i uruchomienie na zdalnym urządzeniu
```bash
./install_remote.sh <adres_ssh> -u <użytkownik> -p <ścieżka_na_zdalnym_urządzeniu>
```

Przykład:
```bash
./install_remote.sh 192.168.1.100 -u pi -p /home/pi/UnitApi/mcp/examples/tts
```

Alternatywnie, możesz użyć runnera do uruchomienia serwera na zdalnym urządzeniu:
```bash
python tts_server_runner.py <adres_ssh> -u <użytkownik> -p <ścieżka_do_tts_server.py>
```

## Wymagania
- Python 3
- `pyttsx3` (na serwerze TTS)
- `aiohttp` (na serwerze TTS)
- `paramiko` (na komputerze uruchamiającym runnera)
- `requests` (na kliencie)
- `SpeechRecognition` i `pyaudio` (dla funkcji STT, instalowane przez install_minimal_ollama.sh)

## Opis działania
- Serwer TTS nasłuchuje na porcie 8081 i odtwarza przesłany tekst na głośniku.
- Serwer STT nasłuchuje na porcie 8082, nagrywa dźwięk z mikrofonu i konwertuje go na tekst.
- Klient pobiera prognozę pogody z lokalnego modelu Ollama (endpoint http://localhost:11434/api/generate) i przesyła ją do serwera TTS.
- Klient UnitMCP obsługuje zarówno funkcje TTS jak i STT, umożliwiając pełną pętlę komunikacji: mowa → tekst → Ollama → tekst → mowa.
- Runner pozwala uruchomić serwer TTS na zdalnym urządzeniu przez SSH.

Każdy plik można uruchomić osobno zgodnie z powyższą instrukcją.
