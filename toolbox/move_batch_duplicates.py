#!/usr/bin/env python3
import os
import filecmp
import shutil

def get_subfolders(path, depth):
    subfolders = []
    for root, dirs, files in os.walk(path):
        rel = os.path.relpath(root, path)
        if rel == ".":
            current_depth = 0
        else:
            current_depth = rel.count(os.sep) + 1
        if current_depth > depth:
            dirs[:] = []
            continue
        if current_depth == depth:
            subfolders.append(root)
    return subfolders

def count_files(folder):
    count = 0
    for _, _, files in os.walk(folder):
        count += len(files)
    return count

def folders_are_equal(folder1, folder2):
    cmp = filecmp.dircmp(folder1, folder2)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    for fname in cmp.common_files:
        f1 = os.path.join(folder1, fname)
        f2 = os.path.join(folder2, fname)
        if not filecmp.cmp(f1, f2, shallow=False):
            return False
    if cmp.common_dirs:
        for d in cmp.common_dirs:
            sd1 = os.path.join(folder1, d)
            sd2 = os.path.join(folder2, d)
            if not folders_are_equal(sd1, sd2):
                return False
    return True

def main():
    dir1 = input("Enter path to the first folder: ").strip()
    dir2 = input("Enter path to the second folder: ").strip()
    depth = 2
    BATCH_LIMIT = 100

    subfolders1 = get_subfolders(dir1, depth)
    subfolders2 = get_subfolders(dir2, depth)

    rel_to_abs1 = {os.path.relpath(f, dir1): f for f in subfolders1}
    rel_to_abs2 = {os.path.relpath(f, dir2): f for f in subfolders2}

    common = list(set(rel_to_abs1.keys()) & set(rel_to_abs2.keys()))
    batch = []
    for idx, rel in enumerate(common, 1):
        f1 = rel_to_abs1[rel]
        f2 = rel_to_abs2[rel]
        print(f"Scanning [{idx}/{len(common)}]: {f1} <-> {f2}")
        files1 = count_files(f1)
        files2 = count_files(f2)
        if folders_are_equal(f1, f2):
            batch.append((f1, f2, files1, files2))
            if len(batch) == BATCH_LIMIT:
                break

    if not batch:
        print("No identical folders found in this batch.")
        return

    print(f"Found {len(batch)} identical subfolder pairs:")
    print(f"{'#':<3} {'Folder 2':<40} {'Files2':<6}")
    print('-'*60)
    for idx, (f1, f2, files1, files2) in enumerate(batch, 1):
        print(f"{idx:<3} {f2:<40} {files2:<6}")

    print("\nWhich directory do you want to move duplicates from?")
    print("1 - First directory (left)")
    print("2 - Second directory (right, listed above)")
    choice = input("Enter 1 or 2 (default 2): ").strip()
    if choice == '1':
        to_move = [(f1, dir2) for (f1, f2, _, _) in batch]
    else:
        to_move = [(f2, dir1) for (f1, f2, _, _) in batch]

    resp = input(f"Move ALL {len(to_move)} folders to a 'duplicated' subfolder in the other directory? [y/N]: ").strip().lower()
    if resp == 'y':
        for src, dest_root in to_move:
            rel = os.path.relpath(src, start=dir1 if choice=='1' else dir2)
            duplicated_dir = os.path.join(dest_root, 'duplicated', rel)
            os.makedirs(os.path.dirname(duplicated_dir), exist_ok=True)
            shutil.move(src, duplicated_dir)
            print(f"Moved {src} -> {duplicated_dir}")
    else:
        print("No folders moved.")

if __name__ == "__main__":
    main()
