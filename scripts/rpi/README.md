Skrypt jest w pełni automatyczny, nie wymaga interakcji, rozpoznaje wersję systemu i automatycznie dostosowuje się do Raspberry Pi OS Stretch lub nowszych wersji.

### Główne funkcje skryptu:

1. **Aktualizacja repozytoriów** - naprawia przestarzałe źródła w Raspberry Pi OS Stretch
2. **Aktualizacja certyfikatów SSL** - rozwiązuje problemy z "server certificate verification failed"
3. **Konfiguracja Git** - poprawia ustawienia SSL dla Git
4. **Instalacja/aktualizacja Pythona** - instaluje najnowszą dostępną wersję Pythona dla danego systemu
5. **Instalacja popularnych pakietów** - instaluje narzędzia systemowe, sieciowe i biblioteki programistyczne
6. **Pełna aktualizacja systemu** - wykonuje upgrade i dist-upgrade

### Elastyczne opcje:

```
-h, --help              Wyświetl pomoc
-u, --user UŻYTKOWNIK   Nazwa użytkownika SSH (domyślnie: pi)
-s, --server IP         Adres IP serwera (domyślnie: 192.168.188.154)
-p, --password HASŁO    Hasło do logowania SSH
-P, --port PORT         Port SSH (domyślnie: 22)
-i, --identity PLIK     Plik klucza prywatnego do autoryzacji
-l, --local             Uruchom lokalnie zamiast przez SSH
--skip-update           Pomiń aktualizację repozytoriów
--skip-packages         Pomiń instalację pakietów
--skip-python           Pomiń instalację/aktualizację Pythona
--skip-git              Pomiń konfigurację Git
--skip-certs            Pomiń aktualizację certyfikatów
--only-certs            Wykonaj tylko aktualizację certyfikatów
--only-update           Wykonaj tylko aktualizację repozytoriów
```

### Przykłady użycia:

```bash
# Wykonaj wszystko z logowaniem hasłem:
./rpi-setup.sh --user pi --server 192.168.188.154 --password raspberry

# Zaktualizuj tylko certyfikaty (rozwiązanie problemu z git):
./rpi-setup.sh --user pi --server 192.168.188.154 --password raspberry --only-certs

# Wykonaj tylko aktualizację repozytoriów:
./rpi-setup.sh --user pi --server 192.168.188.154 --identity ~/.ssh/id_rsa --only-update

# Pełna instalacja z pominięciem Pythona:
./rpi-setup.sh --user pi --server 192.168.188.154 --password raspberry --skip-python
```

