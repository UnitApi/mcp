#!/bin/bash

# Skrypt do naprawy problemów z certyfikatami i synchronizacji czasu
# Przeznaczony do uruchomienia bezpośrednio na Raspberry Pi
# Użycie: sudo bash fix_certificates.sh

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania komunikatów
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUKCES]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[UWAGA]${NC} $1"
}

print_error() {
    echo -e "${RED}[BŁĄD]${NC} $1"
}

print_step() {
    echo -e "\n${PURPLE}===== $1 =====${NC}"
}

print_substep() {
    echo -e "${CYAN}--- $1 ---${NC}"
}

# Sprawdź czy script jest uruchomiony jako root
if [ "$(id -u)" -ne 0 ]; then
    print_error "Ten skrypt musi być uruchomiony jako root lub z sudo."
    print_message "Użyj: sudo bash $0"
    exit 1
fi

# Konfiguracja APT do automatycznego akceptowania zapytań
export DEBIAN_FRONTEND=noninteractive

# Funkcja do aktualizacji repozytoriów
update_repositories() {
    print_step "Aktualizacja repozytoriów"
    
    # Sprawdzanie wersji systemu
    if grep -q "stretch" /etc/os-release; then
        print_warning "Wykryto przestarzały Raspberry Pi OS Stretch. Aktualizacja repozytoriów..."
        
        # Utwórz kopie zapasowe istniejących plików
        print_message "Tworzenie kopii zapasowych istniejących plików konfiguracyjnych..."
        cp /etc/apt/sources.list /etc/apt/sources.list.backup-$(date +%Y%m%d-%H%M%S)
        if [ -f /etc/apt/sources.list.d/raspi.list ]; then
            cp /etc/apt/sources.list.d/raspi.list /etc/apt/sources.list.d/raspi.list.backup-$(date +%Y%m%d-%H%M%S)
        fi

        # Aktualizacja głównego pliku sources.list
        print_message "Aktualizacja głównego pliku sources.list..."
        cat > /etc/apt/sources.list << EOL
# Archiwalne repozytoria Debian dla przestarzałego Raspberry Pi OS Stretch
deb http://archive.debian.org/debian stretch main contrib non-free
deb http://archive.debian.org/debian-security stretch/updates main contrib non-free
EOL

        # Aktualizacja pliku raspi.list
        print_message "Aktualizacja pliku raspi.list..."
        mkdir -p /etc/apt/sources.list.d/
        cat > /etc/apt/sources.list.d/raspi.list << EOL
# Archiwalne repozytoria Raspberry Pi dla przestarzałego OS Stretch
deb http://archive.raspberrypi.org/debian stretch main
EOL

        # Dodanie konfiguracji, aby ignorować błędy weryfikacji dla starych archiwów
        print_message "Dodawanie konfiguracji, aby ignorować błędy weryfikacji dla starych archiwów..."
        cat > /etc/apt/apt.conf.d/99ignore-release-date << EOL
Acquire::Check-Valid-Until "false";
EOL
    fi

    # Aktualizacja listy pakietów
    print_substep "Aktualizacja list pakietów..."
    apt-get update -y
    
    if [ $? -eq 0 ]; then
        print_success "Repozytoria zostały zaktualizowane pomyślnie!"
    else
        print_error "Wystąpił problem podczas aktualizacji repozytoriów."
        return 1
    fi
    
    return 0
}

# Funkcja do synchronizacji czasu
sync_system_time() {
    print_step "Synchronizacja czasu systemowego"
    
    print_message "Stary czas systemowy: $(date)"
    
    print_substep "Instalacja narzędzi do synchronizacji czasu..."
    apt-get install -y ntpdate ntp
    
    # Zatrzymanie usługi NTP na czas synchronizacji ręcznej
    systemctl stop ntp || true
    
    # Próba synchronizacji czasu z różnymi serwerami NTP
    print_substep "Synchronizacja z serwerem pool.ntp.org..."
    ntpdate pool.ntp.org
    if [ $? -ne 0 ]; then
        print_warning "Nie udało się zsynchronizować z pool.ntp.org. Próba z time.google.com..."
        ntpdate time.google.com
        if [ $? -ne 0 ]; then
            print_warning "Nie udało się zsynchronizować z time.google.com. Próba z time.windows.com..."
            ntpdate time.windows.com
            if [ $? -ne 0 ]; then
                print_error "Nie udało się zsynchronizować czasu z żadnym serwerem NTP."
                print_message "Próba pobrania czasu przez HTTP..."
                
                # Próba ustawienia czasu poprzez HTTP
                if command -v wget &> /dev/null; then
                    TIME=$(wget -qSO- --max-redirect=0 google.com 2>&1 | grep Date: | cut -d' ' -f5-8)
                    if [ -n "$TIME" ]; then
                        date -s "${TIME}Z"
                        print_success "Czas został ustawiony poprzez HTTP!"
                    else
                        print_error "Nie udało się pobrać czasu przez HTTP."
                    fi
                else
                    print_error "Narzędzie wget nie jest dostępne."
                fi
            fi
        fi
    fi
    
    # Wyświetlenie nowego czasu
    print_message "Nowy czas systemowy: $(date)"
    
    # Uruchomienie usługi NTP do ciągłej synchronizacji
    print_substep "Konfiguracja ciągłej synchronizacji czasu..."
    systemctl start ntp
    systemctl enable ntp
    
    print_success "Konfiguracja synchronizacji czasu zakończona!"
    return 0
}

# Funkcja do aktualizacji certyfikatów SSL
update_certificates() {
    print_step "Aktualizacja certyfikatów SSL"
    
    print_substep "Instalacja pakietu ca-certificates..."
    apt-get install -y ca-certificates openssl
    
    print_substep "Aktualizacja certyfikatów systemowych..."
    update-ca-certificates --fresh
    
    print_substep "Pobieranie najnowszych certyfikatów z curl.se..."
    apt-get install -y curl
    curl -k https://curl.se/ca/cacert.pem -o /etc/ssl/certs/ca-certificates.crt
    
    if [ $? -eq 0 ]; then
        print_success "Certyfikaty SSL zostały zaktualizowane pomyślnie!"
    else
        print_warning "Wystąpił problem podczas pobierania certyfikatów z curl.se."
        print_message "Próba alternatywnego źródła certyfikatów..."
        
        apt-get install -y wget
        wget --no-check-certificate -O /etc/ssl/certs/ca-certificates.crt https://curl.se/ca/cacert.pem
        
        if [ $? -eq 0 ]; then
            print_success "Certyfikaty SSL zostały zaktualizowane pomyślnie (źródło alternatywne)!"
        else
            print_error "Nie udało się zaktualizować certyfikatów SSL."
            return 1
        fi
    fi
    
    print_success "Aktualizacja certyfikatów zakończona!"
    return 0
}

# Funkcja do konfiguracji pip
configure_pip() {
    print_step "Konfiguracja pip do obsługi problematycznych certyfikatów"
    
    # Konfiguracja globalna pip
    print_substep "Konfiguracja globalna pip..."
    mkdir -p /etc/pip
    cat > /etc/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL

    # Konfiguracja dla bieżącego użytkownika (w trybie sudo to root)
    CURRENT_USER=$(logname 2>/dev/null || echo ${SUDO_USER:-root})
    CURRENT_HOME=$(getent passwd $CURRENT_USER | cut -d: -f6)
    
    if [ -n "$CURRENT_HOME" ] && [ -d "$CURRENT_HOME" ]; then
        print_substep "Konfiguracja pip dla użytkownika $CURRENT_USER..."
        mkdir -p $CURRENT_HOME/.config/pip
        cat > $CURRENT_HOME/.config/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL
        chown -R $CURRENT_USER:$(id -gn $CURRENT_USER 2>/dev/null || echo $CURRENT_USER) $CURRENT_HOME/.config/pip
    fi
    
    # Konfiguracja dla użytkownika pi, jeśli istnieje
    if id "pi" &>/dev/null; then
        print_substep "Konfiguracja pip dla użytkownika pi..."
        mkdir -p /home/pi/.config/pip
        cat > /home/pi/.config/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL
        chown -R pi:pi /home/pi/.config/pip
    fi
    
    # Konfiguracja dla roota
    print_substep "Konfiguracja pip dla użytkownika root..."
    mkdir -p /root/.config/pip
    cat > /root/.config/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL
    
    print_success "Konfiguracja pip została zaktualizowana dla obsługi problematycznych certyfikatów!"
    
    # Instrukcje użycia
    print_message "Aby zainstalować pakiety z pominięciem weryfikacji certyfikatu, możesz teraz używać standardowego polecenia:"
    print_message "pip install <nazwa-pakietu>"
    print_message "lub"
    print_message "pip install -r requirements.txt"
    
    return 0
}

# Funkcja konfiguracji Git
configure_git() {
    print_step "Konfiguracja Git dla obsługi problematycznych certyfikatów"
    
    print_substep "Instalacja Git..."
    apt-get install -y git
    
    print_substep "Wykrywanie obsługiwanego backendu SSL w Git..."
    # Sprawdźmy, jakie backendy SSL są obsługiwane
    local SUPPORTED_SSL=$(git -c http.sslBackend=invalid 2>&1 | grep -o "Supported SSL backends:.*" | sed 's/Supported SSL backends: *//')

    print_message "Wykryte obsługiwane backendy SSL: $SUPPORTED_SSL"

    if echo "$SUPPORTED_SSL" | grep -q "openssl"; then
        print_message "Konfiguracja Git dla backendu OpenSSL..."
        git config --system http.sslBackend openssl
    elif echo "$SUPPORTED_SSL" | grep -q "gnutls"; then
        print_message "Konfiguracja Git dla backendu GnuTLS..."
        git config --system --unset http.sslBackend 2>/dev/null || true
    else
        print_message "Nie wykryto ani OpenSSL ani GnuTLS, pomijam konfigurację backendu..."
        git config --system --unset http.sslBackend 2>/dev/null || true
    fi

    print_substep "Konfiguracja wspólnych ustawień bezpieczeństwa Git..."
    git config --system http.sslCAInfo /etc/ssl/certs/ca-certificates.crt
    git config --system http.sslVerify true

    # Aktualizacja lub tworzenie pliku gitconfig
    print_message "Aktualizacja głównego pliku konfiguracyjnego Git..."

    # Sprawdź istniejący plik i zachowaj jego zawartość
    if [ -f /etc/gitconfig ]; then
        # Usuń istniejącą sekcję [http] jeśli istnieje
        sed -i '/^\[http\]/,/^\[/d' /etc/gitconfig
    fi

    # Dodaj nową sekcję [http] na końcu pliku
    cat >> /etc/gitconfig << EOL
[http]
    sslCAInfo = /etc/ssl/certs/ca-certificates.crt
    sslVerify = true
EOL

    print_success "Konfiguracja Git została zakończona pomyślnie!"
    
    # Instrukcje na wypadek problemów
    print_message "Jeśli nadal występują problemy z certyfikatami w Git, możesz użyć:"
    print_message "git -c http.sslVerify=false clone <url>"
    print_message "lub ustawić globalnie (ostrożnie, zmniejsza bezpieczeństwo):"
    print_message "git config --global http.sslVerify false"
    
    return 0
}

# Główna funkcja
main() {
    print_step "Rozpoczęcie naprawy problemów z certyfikatami i synchronizacją czasu"
    print_message "Data: $(date)"
    print_message "Hostname: $(hostname)"
    print_message "System: $(cat /etc/os-release | grep PRETTY_NAME | cut -d '=' -f 2 | tr -d '"')"
    
    # Aktualizacja repozytoriów
    update_repositories || print_warning "Wystąpiły problemy z aktualizacją repozytoriów, ale kontynuujemy..."
    
    # Synchronizacja czasu
    sync_system_time || print_warning "Wystąpiły problemy z synchronizacją czasu, ale kontynuujemy..."
    
    # Aktualizacja certyfikatów
    update_certificates || print_warning "Wystąpiły problemy z aktualizacją certyfikatów, ale kontynuujemy..."
    
    # Konfiguracja pip
    configure_pip || print_warning "Wystąpiły problemy z konfiguracją pip, ale kontynuujemy..."
    
    # Konfiguracja Git
    configure_git || print_warning "Wystąpiły problemy z konfiguracją Git, ale kontynuujemy..."
    
    print_step "Naprawa zakończona!"
    print_message "Data zakończenia: $(date)"
    
    # Podsumowanie
    print_success "System został skonfigurowany do obsługi problemów z certyfikatami i synchronizacją czasu."
    print_message "Teraz powinieneś móc używać pip i git bez problemów z certyfikatami."
    
    # Informacja o restarcie
    print_warning "Zaleca się restart systemu dla pewności, że wszystkie zmiany zostaną zastosowane:"
    print_message "sudo reboot"
    
    return 0
}

# Uruchomienie głównej funkcji
main
exit $?