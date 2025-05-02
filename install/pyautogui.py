#!/usr/bin/env python3
import sys
import subprocess
import platform


def install_pyautogui():
    """
    Instaluje PyAutoGUI z odpowiednimi zależnościami systemowymi.
    """
    print("Rozpoczynam instalację PyAutoGUI...")

    # Lista wymaganych pakietów
    system = platform.system().lower()
    additional_packages = []

    if system == 'linux':
        # Pakiety wymagane na Linuksie
        additional_packages = [
            'python3-tk',  # Tkinter
            'python3-dev',  # Pliki nagłówkowe Pythona
            'python3-pil',  # Pillow
            'scrot',  # Screen capture dla PyAutoGUI
            'python3-xlib'  # Wsparcie X11
        ]

        # Próba instalacji pakietów systemowych
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y'] + additional_packages, check=True)
        except subprocess.CalledProcessError:
            print("Uwaga: Nie udało się zainstalować wszystkich pakietów systemowych.")

    elif system == 'darwin':  # macOS
        # Dla macOS możemy użyć brew
        try:
            subprocess.run(['brew', 'install', 'python-tk@3.9'], check=True)
        except subprocess.CalledProcessError:
            print("Uwaga: Nie udało się zainstalować dodatkowych zależności przez Homebrew.")

    # Instalacja PyAutoGUI i zależności Pythona
    pip_packages = [
        'pyautogui',
        'pillow',
        'python-xlib',  # dla Linuksa
        'numpy'
    ]

    try:
        # Użycie pip3 dla większej kompatybilności
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + pip_packages, check=True)

        print("\n✅ Instalacja PyAutoGUI zakończona sukcesem!")

        # Weryfikacja instalacji
        try:
            import pyautogui
            import pkg_resources
            print(f"Zainstalowana wersja PyAutoGUI: {pkg_resources.get_distribution('pyautogui').version}")
        except (ImportError, pkg_resources.DistributionNotFound):
            print("❌ Weryfikacja instalacji nie powiodła się.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas instalacji: {e}")
        sys.exit(1)


def main():
    print("\n===== Instalator PyAutoGUI =====")
    print("Ten skrypt zainstaluje PyAutoGUI i niezbędne zależności.")
    print("Może wymagać uprawnień administratora.\n")

    install_pyautogui()


if __name__ == "__main__":
    main()