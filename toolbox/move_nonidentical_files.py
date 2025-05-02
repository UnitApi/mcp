#!/usr/bin/env python3
import os
import shutil
import hashlib

def get_level2_folders(path):
    # Returns all subfolders at depth 2: path/*/*
    level2 = []
    for root, dirs, files in os.walk(path):
        rel = os.path.relpath(root, path)
        if rel == ".": continue
        if rel.count(os.sep) == 1:
            level2.append(root)
        elif rel.count(os.sep) > 1:
            dirs[:] = []  # Don't go deeper
    return level2

def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_different_files(src_folder, tgt_folder, src_root):
    # Returns list of (src_file, rel_path) that differ or are missing in tgt_folder
    diff_files = []
    for dirpath, dirs, files in os.walk(src_folder):
        rel = os.path.relpath(dirpath, src_root)
        tgt_dir = os.path.join(tgt_folder, rel)
        for fname in files:
            src_file = os.path.join(dirpath, fname)
            tgt_file = os.path.join(tgt_dir, fname)
            if os.path.exists(tgt_file):
                if file_hash(src_file) != file_hash(tgt_file):
                    diff_files.append((src_file, rel, fname))
            else:
                diff_files.append((src_file, rel, fname))
    return diff_files

def main():
    dir1 = input("Enter path to the first folder: ").strip()
    dir2 = input("Enter path to the second folder: ").strip()
    print("To which directory should non-identical files be moved?")
    print(f"1 - {dir1}")
    print(f"2 - {dir2}")
    target_choice = input("Enter 1 or 2 (default 2): ").strip()
    if target_choice == '1':
        target_root = dir1
        source_root = dir2
    else:
        target_root = dir2
        source_root = dir1
    batch_limit = 100

    # Level 2 folder matching
    src_level2 = get_level2_folders(source_root)
    tgt_level2 = get_level2_folders(target_root)
    rel_to_src = {os.path.relpath(f, source_root): f for f in src_level2}
    rel_to_tgt = {os.path.relpath(f, target_root): f for f in tgt_level2}
    common = list(set(rel_to_src.keys()) & set(rel_to_tgt.keys()))
    moved = 0
    for idx, rel in enumerate(common, 1):
        src_folder = rel_to_src[rel]
        tgt_folder = rel_to_tgt[rel]
        print(f"Comparing [{idx}/{len(common)}]: {src_folder} <-> {tgt_folder}")
        diff_files = get_different_files(src_folder, tgt_folder, source_root)
        for src_file, rel_path, fname in diff_files:
            dest_dir = os.path.join(tgt_folder, 'duplicated', rel_path)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, fname)
            shutil.move(src_file, dest)
            print(f"Moved {src_file} -> {dest}")
            moved += 1
            if moved >= batch_limit:
                print(f"Batch limit {batch_limit} reached.")
                return
    print(f"Done. Moved {moved} non-identical files from {source_root} to {target_root}/duplicated.")

if __name__ == "__main__":
    main()
