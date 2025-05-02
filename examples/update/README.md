## Features of the script:

1. Supports different version declaration formats:
   - `__version__ = version = "0.1.3"`
   - `__version__ = "0.1.8"`
   - `version = "0.1.3"`

2. Provides multiple update methods:
   - Incrementing major, minor, or patch versions
   - Setting a specific version directly
   - Creating prerelease versions (alpha, beta, rc)

3. Creates backups by default to prevent data loss

## How to use it:

```bash
# Increment patch version (0.1.8 → 0.1.9)
python update_version.py -f path/to/your/file.py

# Increment minor version (0.1.8 → 0.2.0)
python update_version.py -f path/to/your/file.py -t minor

# Increment major version (0.1.8 → 1.0.0)
python update_version.py -f path/to/your/file.py -t major

# Set a specific version
python update_version.py -f path/to/your/file.py -v 0.2.5

# Skip creating a backup file
python update_version.py -f path/to/your/file.py --no-backup
```

# update/

Folder zawiera narzędzia do aktualizacji projektu i zarządzania wersjami.

**Skrypty bash:**

- `duplicated.sh`, `pip.sh`, `requirements.sh` – po reorganizacji są w scripts/.
- `git.sh` – automatyzuje operacje git (push, tag, itp.).
- `pypi.sh` – automatyzuje publikację do PyPI.
- `src.sh`, `project.sh`, `changelog.py` – narzędzia do aktualizacji wersji kodu i changeloga.

**Użycie:**

```bash
bash update/pypi.sh
```

**Narzędzia Python:**

- `duplicated.py`, `requirements.py`, `versions.py` – narzędzia do analizy i zarządzania zależnościami oraz wersjami.

---

Więcej szczegółów w nagłówkach poszczególnych skryptów.

---

Aby uruchomić skrypt, przejdź do głównego katalogu projektu i użyj:

```bash
bash scripts/<nazwa_skryptu.sh>
```

Lub dla narzędzi Python:

```bash
python update/<nazwa_skryptu.py>
```
