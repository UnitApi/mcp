#!/bin/bash
# Skrypt do czyszczenia systemu Fedora
# 1. Szuka dużych plików w ~/
# 2. Szuka nieużywanych od roku aplikacji RPM
# 3. Pozwala usuwać pliki i odinstalowywać aplikacje po numerach

set -e

HOME_DIR="$HOME"
MIN_SIZE="100M"    # Minimalny rozmiar pliku do pokazania
MAX_FILES=20        # Maksymalna liczba plików do pokazania

# 1. Szukanie dużych plików

echo "\n=== DUŻE PLIKI W $HOME_DIR ==="
mapfile -t BIG_FILES < <(find "$HOME_DIR" -type f -size +$MIN_SIZE -printf '%s %p\n' 2>/dev/null | sort -nr | head -n $MAX_FILES)

if [ ${#BIG_FILES[@]} -eq 0 ]; then
    echo "Brak dużych plików."
else
    i=1
    for entry in "${BIG_FILES[@]}"; do
        size=$(echo "$entry" | awk '{print $1}')
        file=$(echo "$entry" | cut -d' ' -f2-)
        human=$(numfmt --to=iec $size)
        echo "$i) $file ($human)"
        ((i++))
    done
    echo "\nPodaj numery plików do usunięcia (oddzielone spacją, Enter by pominąć):"
    read -r FILES_TO_DELETE
    for num in $FILES_TO_DELETE; do
        idx=$((num-1))
        file=$(echo "${BIG_FILES[$idx]}" | cut -d' ' -f2-)
        if [ -f "$file" ]; then
            rm -i "$file"
            echo "Usunięto: $file"
        fi
    done
fi

# 2. Szukanie nieużywanych aplikacji RPM
# Uwaga: sprawdzamy datę ostatniego użycia pliku wykonywalnego z pakietu

echo "\n=== NIEUŻYWANE APLIKACJE (RPM) OD ROKU ==="
YEAR_AGO=$(date --date='1 year ago' +%s)
mapfile -t PKGS < <(rpm -qa --qf '%{NAME}\n' | sort)
UNUSED_PKGS=()
for pkg in "${PKGS[@]}"; do
    BIN=$(rpm -ql "$pkg" | grep -E '^/usr/bin/' | head -n 1)
    if [ -n "$BIN" ] && [ -f "$BIN" ]; then
        ATIME=$(stat -c %X "$BIN" 2>/dev/null || echo 0)
        if [ "$ATIME" -lt "$YEAR_AGO" ]; then
            UNUSED_PKGS+=("$pkg:$BIN")
        fi
    fi
    if [ ${#UNUSED_PKGS[@]} -ge 20 ]; then
        break
    fi
    # Ograniczamy do 20 dla szybkości
    # Możesz usunąć powyższy warunek, by sprawdzić wszystkie
done

if [ ${#UNUSED_PKGS[@]} -eq 0 ]; then
    echo "Brak nieużywanych aplikacji."
else
    i=1
    for entry in "${UNUSED_PKGS[@]}"; do
        pkg=$(echo "$entry" | cut -d: -f1)
        bin=$(echo "$entry" | cut -d: -f2-)
        echo "$i) $pkg (bin: $bin)"
        ((i++))
    done
    echo "\nPodaj numery aplikacji do odinstalowania (oddzielone spacją, Enter by pominąć):"
    read -r PKGS_TO_REMOVE
    for num in $PKGS_TO_REMOVE; do
        idx=$((num-1))
        pkg=$(echo "${UNUSED_PKGS[$idx]}" | cut -d: -f1)
        sudo dnf remove -y "$pkg"
        echo "Odinstalowano: $pkg"
    done
fi
