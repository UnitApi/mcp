#!/bin/bash
# Usuń poprzednie pliki

echo "Starting publication process..."
#flatedit

python -m venv venv
source venv/bin/activate


# Upewnij się że mamy najnowsze narzędzia
pip install --upgrade pip build twine

# Sprawdź czy jesteśmy w virtualenv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Aktywuj najpierw virtualenv!"
    exit 1
fi

pip install -r requirements.txt

python update/changelog.py
bash update/git.sh
