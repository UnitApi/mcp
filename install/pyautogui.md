# PyAutoGUI Installer Script

## Opis
Ten skrypt automatyzuje instalację biblioteki PyAutoGUI i jej zależności systemowych, szczególnie przydatny w środowiskach Linux.

## Wymagania
- Python 3.x
- Uprawnienia administratora (sudo) w systemach Linux
- pip
- Środowisko wirtualne (zalecane)

## Funkcje
- Automatyczna instalacja PyAutoGUI
- Instalacja dodatkowych zależności systemowych
- Wsparcie dla systemów Linux, macOS
- Weryfikacja poprawności instalacji

## Użycie
```bash
python install_pyautogui.py
```

## Uwagi
- Na systemach Linux może wymagać hasła sudo
- Sprawdza i instaluje niezbędne pakiety systemowe
- Aktualizuje pip przed instalacją pakietów

## Rozwiązywanie problemów

### Typowe problemy i ich rozwiązania

1. **Błędy repozytorium apt**
   - Jeśli widzisz błędy związane z kluczami GPG, możesz je zignorować
   - Problemy z repozytorium nie powinny wpłynąć na instalację PyAutoGUI

2. **Konflikty zależności**
   - Skrypt wyświetla ostrzeżenia o konfliktach zależności
   - Nie blokują one instalacji PyAutoGUI
   - Możesz rozwiązać je później, instalując brakujące pakiety

3. **Problemy z uprawnieniami**
   ```bash
   # Jeśli masz problemy z uprawnieniami, użyj:
   sudo python3 install_pyautogui.py
   # Lub
   python3 -m pip install --user pyautogui
   ```

4. **Instalacja w środowisku wirtualnym (zalecane)**
   ```bash
   # Tworzenie środowiska wirtualnego
   python3 -m venv myenv
   source myenv/bin/activate
   
   # Instalacja w środowisku wirtualnym
   pip install pyautogui
   ```

5. **Wymagane pakiety systemowe**
   ```bash
   # Dla Debian/Ubuntu
   sudo apt-get install -y \
     python3-tk \
     python3-dev \
     python3-pil \
     scrot \
     python3-xlib
   ```

## Zależności
- pyautogui
- pillow
- python-xlib
- numpy
- python3-Xlib
- pymsgbox
- pytweening
- pyscreeze
- pygetwindow

## Licencja
Skrypt jest udostępniany bez ograniczeń licencyjnych.

## Uwaga
