import os
import hashlib
import shutil
from pathlib import Path

MEDIA_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.mp4', '.mov', '.avi', '.mp3', '.wav', '.flac', '.mkv', '.webm'}

def file_hash(path, chunk_size=65536):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def collect_media_files(root_dirs):
    files = []
    for root_dir in root_dirs:
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in MEDIA_EXTENSIONS:
                    full_path = os.path.join(dirpath, fname)
                    files.append(full_path)
    return files

def main():
    print("Podaj ścieżki do katalogów do przeszukania (oddzielone przecinkami):")
    src_dirs = [d.strip() for d in input().split(',') if d.strip()]
    print("Podaj ścieżkę do katalogu docelowego na duplikaty:")
    dup_dir = input().strip()
    if not src_dirs or not dup_dir:
        print("Błąd: wymagane są katalogi źródłowe i docelowy.")
        return
    
    print("Indeksowanie plików...")
    files = collect_media_files(src_dirs)
    print(f"Znaleziono {len(files)} plików mediów.")

    # Map: (size, hash) -> list of files
    hash_map = {}
    for f in files:
        try:
            size = os.path.getsize(f)
            h = file_hash(f)
            key = (size, h)
            hash_map.setdefault(key, []).append(f)
        except Exception as e:
            print(f"Błąd przy pliku {f}: {e}")

    moved = 0
    for (size, h), paths in hash_map.items():
        if len(paths) > 1:
            # Sortuj po dacie modyfikacji (najstarszy zostaje, młodsze idą do duplikatów)
            paths_sorted = sorted(paths, key=lambda p: os.path.getmtime(p))
            original = paths_sorted[0]
            for dup in paths_sorted[1:]:
                rel_path = os.path.relpath(dup, start=Path(dup).anchor)
                dest = os.path.join(dup_dir, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(dup, dest)
                print(f"Przeniesiono duplikat: {dup} -> {dest}")
                moved += 1
    print(f"Przeniesiono {moved} duplikatów.")

if __name__ == "__main__":
    main()
