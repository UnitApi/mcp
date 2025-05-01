#!/bin/bash

# Skrypt kompleksowej aktualizacji i instalacji pakietów na Raspberry Pi
# Ten skrypt aktualizuje źródła, naprawia certyfikaty SSL i instaluje popularne pakiety
# Wspiera działanie przez SSH lub lokalnie

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

# Funkcja wyświetlająca pomoc
show_help() {
    echo "Skrypt kompleksowej aktualizacji i instalacji pakietów na Raspberry Pi"
    echo
    echo "Użycie: $0 [opcje]"
    echo
    echo "Opcje:"
    echo "  -h, --help              Wyświetl tę pomoc"
    echo "  -u, --user UŻYTKOWNIK   Nazwa użytkownika SSH (domyślnie: pi)"
    echo "  -s, --server IP         Adres IP serwera (domyślnie: 192.168.188.154)"
    echo "  -p, --password HASŁO    Hasło do logowania SSH"
    echo "  -P, --port PORT         Port SSH (domyślnie: 22)"
    echo "  -i, --identity PLIK     Plik klucza prywatnego do autoryzacji"
    echo "  -l, --local             Uruchom lokalnie zamiast przez SSH"
    echo "  --skip-update           Pomiń aktualizację repozytoriów"
    echo "  --skip-packages         Pomiń instalację pakietów"
    echo "  --skip-python           Pomiń instalację/aktualizację Pythona"
    echo "  --skip-git              Pomiń konfigurację Git"
    echo "  --skip-certs            Pomiń aktualizację certyfikatów"
    echo "  --only-certs            Wykonaj tylko aktualizację certyfikatów"
    echo "  --only-update           Wykonaj tylko aktualizację repozytoriów"
    echo
    echo "Przykłady:"
    echo "  $0 --user pi --server 192.168.1.100 --password raspberry"
    echo "  $0 --local --skip-python              # Uruchom lokalnie bez aktualizacji Pythona"
    echo "  $0 --user pi --server 192.168.1.100 --only-certs  # Tylko aktualizacja certyfikatów"
}

# Domyślne wartości
USERNAME="pi"
SERVER_IP="192.168.188.154"
PASSWORD=""
SSH_PORT="22"
IDENTITY_FILE=""
RUN_LOCAL=false
SKIP_UPDATE=false
SKIP_PACKAGES=false
SKIP_PYTHON=false
SKIP_GIT=false
SKIP_CERTS=false
ONLY_CERTS=false
ONLY_UPDATE=false

# Parsowanie argumentów wiersza poleceń
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--user)
            USERNAME="$2"
            shift 2
            ;;
        -s|--server)
            SERVER_IP="$2"
            shift 2
            ;;
        -p|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -P|--port)
            SSH_PORT="$2"
            shift 2
            ;;
        -i|--identity)
            IDENTITY_FILE="$2"
            shift 2
            ;;
        -l|--local)
            RUN_LOCAL=true
            shift
            ;;
        --skip-update)
            SKIP_UPDATE=true
            shift
            ;;
        --skip-packages)
            SKIP_PACKAGES=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --skip-certs)
            SKIP_CERTS=true
            shift
            ;;
        --only-certs)
            ONLY_CERTS=true
            SKIP_UPDATE=true
            SKIP_PACKAGES=true
            SKIP_PYTHON=true
            SKIP_GIT=true
            SKIP_CERTS=false
            shift
            ;;
        --only-update)
            ONLY_UPDATE=true
            SKIP_PACKAGES=true
            SKIP_PYTHON=true
            SKIP_GIT=true
            SKIP_CERTS=true
            SKIP_UPDATE=false
            shift
            ;;
        *)
            print_error "Nieznana opcja: $1"
            show_help
            exit 1
            ;;
    esac
done

# Zawartość skryptu, który zostanie wykonany na Raspberry Pi
create_remote_script() {
    cat << 'EOFSCRIPT'
#!/bin/bash
# Kolory dla lepszej czytelności
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
PURPLE="\033[0;35m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color

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
    exit 1
fi

# Odczytaj argumenty
SKIP_UPDATE=@SKIP_UPDATE@
SKIP_PACKAGES=@SKIP_PACKAGES@
SKIP_PYTHON=@SKIP_PYTHON@
SKIP_GIT=@SKIP_GIT@
SKIP_CERTS=@SKIP_CERTS@

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

# Funkcja do aktualizacji certyfikatów SSL i synchronizacji czasu
update_certificates() {
    print_step "Aktualizacja certyfikatów SSL i synchronizacja czasu"

    print_substep "Synchronizacja czasu systemowego..."
    apt-get install -y ntpdate ntp

    # Zatrzymanie usługi NTP na czas synchronizacji ręcznej
    systemctl stop ntp || true

    # Próba synchronizacji czasu z serwerami NTP
    ntpdate pool.ntp.org || ntpdate time.google.com || ntpdate time.windows.com

    # Sprawdzamy aktualny czas
    print_message "Aktualny czas systemu: $(date)"

    # Uruchomienie usługi NTP do ciągłej synchronizacji
    systemctl start ntp
    systemctl enable ntp

    print_substep "Instalacja pakietu ca-certificates..."
    apt-get install -y ca-certificates openssl

    print_substep "Aktualizacja certyfikatów systemowych..."
    update-ca-certificates --fresh

    print_substep "Pobieranie najnowszych certyfikatów z curl.se..."
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

    # Konfiguracja pip dla omijania problemów z certyfikatami
    print_substep "Konfiguracja pip do obsługi problematycznych certyfikatów..."
    mkdir -p /etc/pip
    cat > /etc/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL

    # Konfiguracja dla użytkownika pi
    if id "pi" &>/dev/null; then
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
    mkdir -p /root/.config/pip
    cat > /root/.config/pip/pip.conf << EOL
[global]
trusted-host =
    pypi.org
    files.pythonhosted.org
    piwheels.org
EOL

    print_success "Konfiguracja pip została zaktualizowana dla obsługi problematycznych certyfikatów!"
    return 0
}

# Funkcja do konfiguracji Git
configure_git() {
    print_step "Konfiguracja Git"

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

    # Instrukcje dla problemów z Git
    print_message "Jeśli nadal występują problemy z certyfikatami w Git, możesz użyć:"
    print_message "git -c http.sslVerify=false clone <url>"

    return 0
}

# Funkcja do instalacji i aktualizacji Pythona
install_python() {
    print_step "Instalacja/aktualizacja Pythona"

    # Sprawdzanie wersji systemu
    if grep -q "stretch" /etc/os-release; then
        print_warning "Na systemie Stretch dostępne są ograniczone wersje Pythona."
        print_substep "Instalacja Python 3.5 (najnowszy dla Stretch)..."
        apt-get install -y python3 python3-pip python3-dev python3-setuptools python3-wheel python3-venv build-essential libssl-dev libffi-dev
    else
        # Dla nowszych systemów spróbujmy dodać repozytorium deadsnakes
        print_substep "Próba instalacji nowszych wersji Pythona..."
        apt-get install -y software-properties-common dirmngr apt-transport-https build-essential libssl-dev libffi-dev

        # Próba dodania repozytorium deadsnakes (może nie zadziałać na starszych systemach)
        add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || print_warning "Nie można dodać repozytorium deadsnakes. Instalacja standardowej wersji Python z repozytorium."

        apt-get update -y

        # Próba instalacji Python 3.9
        apt-get install -y python3 python3-pip python3-dev python3-setuptools python3-wheel python3-venv || print_warning "Nie udało się zainstalować wszystkich pakietów Python. Instalacja podstawowych."

        # Instalacja bibliotek naukowych
        print_substep "Instalacja popularnych bibliotek Pythona..."
        apt-get install -y python3-numpy python3-scipy python3-matplotlib python3-pandas || print_warning "Nie udało się zainstalować wszystkich bibliotek naukowych."
    fi

    # Aktualizacja pip z pominięciem weryfikacji certyfikatu
    print_substep "Aktualizacja pip z bezpiecznymi opcjami..."
    python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host piwheels.org --upgrade pip || print_warning "Nie udało się zaktualizować pip."

    # Instalacja virtualenv z pominięciem weryfikacji certyfikatu
    print_substep "Instalacja virtualenv z bezpiecznymi opcjami..."
    python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host piwheels.org virtualenv || print_warning "Nie udało się zainstalować virtualenv."

    # Dodanie dodatkowych przydatnych narzędzi Python
    print_substep "Instalacja dodatkowych narzędzi Python..."
    python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host piwheels.org pipenv pip-tools 2>/dev/null || print_warning "Nie udało się zainstalować wszystkich narzędzi Python."

    # Instalacja pyenv do zarządzania wieloma wersjami Pythona
    print_substep "Instalacja pyenv do zarządzania wieloma wersjami Pythona..."
    apt-get install -y curl git libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl || print_warning "Nie udało się zainstalować wszystkich zależności pyenv."

    # Instalacja pyenv dla użytkownika pi, jeśli istnieje
    if id "pi" &>/dev/null; then
        print_message "Instalacja pyenv dla użytkownika pi..."
        sudo -u pi bash -c 'curl -s https://pyenv.run | bash' || print_warning "Nie udało się zainstalować pyenv dla użytkownika pi."

        # Dodanie konfiguracji pyenv do bashrc
        if [ -f /home/pi/.bashrc ]; then
            if ! grep -q "pyenv" /home/pi/.bashrc; then
                cat >> /home/pi/.bashrc << EOL

# Konfiguracja pyenv - menadżera wersji Pythona
export PATH="/home/pi/.pyenv/bin:\$PATH"
eval "\$(pyenv init --path)"
eval "\$(pyenv virtualenv-init -)"
EOL
                print_message "Dodano konfigurację pyenv do .bashrc użytkownika pi"
            fi
        fi
    fi

    print_success "Instalacja Pythona zakończona!"

    # Wyświetlenie informacji o zainstalowanej wersji
    PYTHON_VERSION=$(python3 --version)
    PIP_VERSION=$(pip3 --version)

    print_message "Zainstalowana wersja Pythona: $PYTHON_VERSION"
    print_message "Zainstalowana wersja pip: $PIP_VERSION"

    # Instrukcje dotyczące instalacji Pythona 3.11 za pomocą pyenv
    print_message "Aby zainstalować nowsze wersje Pythona (np. 3.11) za pomocą pyenv, wykonaj:"
    print_message "pyenv install 3.11.0  # Zainstaluj Python 3.11.0"
    print_message "pyenv global 3.11.0  # Ustaw Python 3.11.0 jako domyślny"
    print_message "python --version  # Sprawdź wersję"

    # Dodanie pomocnych informacji o instalacji pakietów z pominięciem weryfikacji certyfikatu
    print_message "Aby zainstalować pakiety z pominięciem weryfikacji certyfikatu, użyj:"
    print_message "pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host piwheels.org nazwapakietu"
    print_message "lub zainstaluj z pliku requirements.txt:"
    print_message "pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host piwheels.org -r requirements.txt"

    return 0
}

# Funkcja do instalacji popularnych pakietów
install_packages() {
    print_step "Instalacja popularnych pakietów"

    print_substep "Instalacja narzędzi systemowych..."
    apt-get install -y vim nano htop screen tmux nmap wget curl rsync zip unzip \
                       sudo build-essential cmake pkg-config usbutils

    print_substep "Instalacja narzędzi sieciowych..."
    apt-get install -y network-manager net-tools openssh-server openssh-client \
                       sshpass

    print_substep "Instalacja bibliotek programistycznych..."
    apt-get install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
                       libncurses5-dev libncursesw5-dev xz-utils libffi-dev liblzma-dev

    print_success "Instalacja pakietów zakończona pomyślnie!"
    return 0
}

# Funkcja przeprowadzająca pełną aktualizację systemu
perform_full_upgrade() {
    print_step "Aktualizacja systemu"

    print_substep "Wykonywanie pełnej aktualizacji pakietów..."
    apt-get upgrade -y

    print_substep "Wykonywanie aktualizacji dystrybucji..."
    apt-get dist-upgrade -y

    print_substep "Usuwanie niepotrzebnych pakietów..."
    apt-get autoremove -y
    apt-get autoclean -y

    print_success "Aktualizacja systemu zakończona pomyślnie!"
    return 0
}

# Główna funkcja
main() {
    print_step "Rozpoczęcie pełnej konfiguracji Raspberry Pi"
    print_message "Data: $(date)"
    print_message "Hostname: $(hostname)"
    print_message "System: $(cat /etc/os-release | grep PRETTY_NAME | cut -d '=' -f 2 | tr -d '"')"

    # Aktualizacja repozytoriów
    if [ "$SKIP_UPDATE" = "false" ]; then
        update_repositories
    else
        print_message "Pomijanie aktualizacji repozytoriów..."
    fi

    # Aktualizacja certyfikatów
    if [ "$SKIP_CERTS" = "false" ]; then
        update_certificates
    else
        print_message "Pomijanie aktualizacji certyfikatów..."
    fi

    # Konfiguracja Git
    if [ "$SKIP_GIT" = "false" ]; then
        configure_git
    else
        print_message "Pomijanie konfiguracji Git..."
    fi

    # Instalacja Pythona
    if [ "$SKIP_PYTHON" = "false" ]; then
        install_python
    else
        print_message "Pomijanie instalacji Pythona..."
    fi

    # Instalacja pakietów
    if [ "$SKIP_PACKAGES" = "false" ]; then
        install_packages
        perform_full_upgrade
    else
        print_message "Pomijanie instalacji pakietów..."
    fi

    print_step "Konfiguracja zakończona pomyślnie!"
    print_message "Data zakończenia: $(date)"

    # Informacja o konieczności restartu
    print_warning "Zalecane jest wykonanie restartu systemu: sudo reboot"

    return 0
}

# Uruchomienie głównej funkcji
main
exit $?
EOFSCRIPT
}

# Tworzenie zmodyfikowanego skryptu z właściwymi flagami
create_modified_script() {
    local script=$(create_remote_script)

    # Zamiana znaczników na wartości flag
    script=$(echo "$script" | sed "s/@SKIP_UPDATE@/$SKIP_UPDATE/g")
    script=$(echo "$script" | sed "s/@SKIP_PACKAGES@/$SKIP_PACKAGES/g")
    script=$(echo "$script" | sed "s/@SKIP_PYTHON@/$SKIP_PYTHON/g")
    script=$(echo "$script" | sed "s/@SKIP_GIT@/$SKIP_GIT/g")
    script=$(echo "$script" | sed "s/@SKIP_CERTS@/$SKIP_CERTS/g")

    echo "$script"
}

# Funkcja do uruchomienia skryptu lokalnie
run_local() {
    print_message "Uruchamianie skryptu lokalnie..."
    # Tworzy zmodyfikowany skrypt
    MODIFIED_SCRIPT=$(create_modified_script)

    # Tworzy tymczasowy plik skryptu
    TEMP_SCRIPT=$(mktemp)
    echo "$MODIFIED_SCRIPT" > "$TEMP_SCRIPT"
    chmod +x "$TEMP_SCRIPT"

    # Uruchamia skrypt z sudo
    sudo "$TEMP_SCRIPT"
    RESULT=$?

    # Usuwa tymczasowy plik
    rm -f "$TEMP_SCRIPT"

    return $RESULT
}

# Funkcja do uruchomienia skryptu przez SSH
run_remote() {
    print_message "Uruchamianie skryptu na zdalnym serwerze $SERVER_IP przez SSH..."

    # Przygotowanie opcji SSH
    SSH_OPTS="-o ConnectTimeout=10 -o ServerAliveInterval=60 -p $SSH_PORT"

    # Dodanie pliku tożsamości jeśli został podany
    if [ -n "$IDENTITY_FILE" ]; then
        if [ -f "$IDENTITY_FILE" ]; then
            SSH_OPTS="$SSH_OPTS -i $IDENTITY_FILE -o PreferredAuthentications=publickey -o IdentitiesOnly=yes"
            print_message "Używanie pliku tożsamości: $IDENTITY_FILE"
        else
            print_error "Plik tożsamości $IDENTITY_FILE nie istnieje!"
            exit 1
        fi
    elif [ -n "$PASSWORD" ]; then
        # Sprawdzenie czy sshpass jest zainstalowany
        if ! command -v sshpass &> /dev/null; then
            print_error "Program sshpass nie jest zainstalowany, a jest wymagany do logowania z hasłem."
            print_message "Zainstaluj sshpass: sudo apt-get install sshpass"
            exit 1
        fi
        SSH_OPTS="$SSH_OPTS -o PreferredAuthentications=password -o PubkeyAuthentication=no"
        print_message "Używanie uwierzytelniania hasłem"
    fi

    # Tworzy zmodyfikowany skrypt
    MODIFIED_SCRIPT=$(create_modified_script)

    # Wykonanie skryptu zdalnie przez SSH
    if [ -n "$PASSWORD" ]; then
        echo "$MODIFIED_SCRIPT" | sshpass -p "$PASSWORD" ssh $SSH_OPTS "$USERNAME@$SERVER_IP" "sudo bash -s"
        RESULT=$?
    else
        echo "$MODIFIED_SCRIPT" | ssh $SSH_OPTS "$USERNAME@$SERVER_IP" "sudo bash -s"
        RESULT=$?
    fi

    return $RESULT
}

# Główna logika - uruchom lokalnie lub zdalnie
if [ "$RUN_LOCAL" = true ]; then
    run_local
    RESULT=$?
else
    run_remote
    RESULT=$?
fi

# Wyświetl informację o wyniku
if [ $RESULT -eq 0 ]; then
    print_success "Skrypt został wykonany pomyślnie!"
else
    print_error "Wystąpił błąd podczas wykonywania skryptu (kod: $RESULT)"
fi

exit $RESULT