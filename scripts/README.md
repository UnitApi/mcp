# Skrypty Bash (`.sh`) – Dokumentacja

Wszystkie skrypty zostały przeniesione do folderu `scripts/`.

---

## Lista skryptów i sposób użycia

- **build.sh** – Buduje projekt lokalnie.  
  `bash build.sh`
- **configure_hardware.sh** – Konfiguruje sprzęt na platformie docelowej (np. Raspberry Pi, PC).  
  `sudo ./configure_hardware.sh`
- **duplicated.sh** – Wyszukuje duplikaty plików lub zależności.  
  `bash duplicated.sh`
- **git.sh** – Ułatwia operacje na repozytorium git.  
  `bash git.sh`
- **install.sh** – Ogólna instalacja zależności/projektu.  
  `bash install.sh`
- **install_fedora.sh** – Instalacja zależności na systemie Fedora.  
  `bash install_fedora.sh`
- **install_macos.sh** – Instalacja zależności na macOS.  
  `bash install_macos.sh`
- **install_models.sh** – Pobiera i instaluje wymagane modele ML.  
  `bash install_models.sh`
- **install_ubuntu.sh** – Instalacja zależności na Ubuntu.  
  `bash install_ubuntu.sh`
- **optimize_rpi.sh** – Optymalizuje system Raspberry Pi do pracy z projektem.  
  `sudo ./optimize_rpi.sh`
- **pip.sh** – Aktualizuje pip i zależności.  
  `bash pip.sh`
- **publish.sh** – Publikuje projekt do repozytorium lub pypi.  
  `bash publish.sh`
- **pyaudio.sh, pyaudio2.sh, pyaudio3.sh** – Instalacja i diagnostyka PyAudio na różnych platformach.  
  `bash pyaudio.sh`
- **python.sh** – Instalacja Pythona i zależności na Fedorze.  
  `bash python.sh`
- **requirements.sh** – Instaluje zależności z requirements.txt.  
  `bash requirements.sh`
- **setup_service.sh** – Konfiguruje usługę systemową (np. systemd).  
  `sudo ./setup_service.sh`
- **spacy.sh** – Instalacja i konfiguracja biblioteki spaCy.  
  `bash spacy.sh`
- **ssh.sh** – Uproszczony wrapper do połączeń SSH.  
  `bash ssh.sh [host]`
- **ssh_connect_wrapper.sh** – Wrapper do skryptów SSH, rozszerza funkcjonalność `ssh.sh`.  
  `bash ssh_connect_wrapper.sh`
- **upgrade.sh** – Aktualizuje środowisko lub zależności.  
  `bash upgrade.sh`
- **version.sh** – Wyświetla wersję projektu.  
  `bash version.sh`

Wszystkie skrypty uruchamiaj z poziomu katalogu scripts:

```bash
cd scripts
bash <nazwa_skryptu.sh>
```

---

Jeśli chcesz szczegółowy opis działania któregoś skryptu, zajrzyj do jego nagłówka lub kodu źródłowego.
