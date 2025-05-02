#!/usr/bin/env python3
import os
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

def folder_hash(folder):
    # Recursively hash all files in a folder (ignoring .git)
    hashes = []
    for dirpath, dirs, files in os.walk(folder):
        if '.git' in dirs:
            dirs.remove('.git')
        for fname in sorted(files):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'rb') as f:
                    content = f.read()
                h = hashlib.sha256(content).hexdigest()
                rel = os.path.relpath(fpath, folder)
                hashes.append((rel, h))
            except Exception as e:
                continue
    return tuple(sorted(hashes))

def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def folder_deep_compare(folder1, folder2, logf):
    files1 = set()
    files2 = set()
    for root, dirs, files in os.walk(folder1):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), folder1)
            files1.add(rel)
    for root, dirs, files in os.walk(folder2):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), folder2)
            files2.add(rel)
    only_in_1 = files1 - files2
    only_in_2 = files2 - files1
    common = files1 & files2
    if only_in_1 or only_in_2:
        logf.write(f"Files only in {folder1}:\n")
        for f in sorted(only_in_1):
            logf.write(f"  {f}\n")
        logf.write(f"Files only in {folder2}:\n")
        for f in sorted(only_in_2):
            logf.write(f"  {f}\n")
    diff_content = []
    for f in sorted(common):
        path1 = os.path.join(folder1, f)
        path2 = os.path.join(folder2, f)
        if file_hash(path1) != file_hash(path2):
            diff_content.append(f)
    if diff_content:
        logf.write(f"Files with different content:\n")
        for f in diff_content:
            logf.write(f"  {f}\n")
    if only_in_1 or only_in_2 or diff_content:
        logf.write("\n")

def main():
    print("Enter folder paths to compare. Just press Enter on an empty line to start the process:")
    folders = []
    while True:
        p = input(f"Path {len(folders)+1}: ").strip()
        if p == '':
            break
        if not os.path.isdir(p):
            print("Not a valid directory!")
            continue
        folders.append(os.path.abspath(p))
    if len(folders) < 2:
        print("Warning: fewer than 2 folders. Comparison may not be meaningful.")
    print("Folders to be compared:")
    for f in folders:
        print(f"  {f}")
    # Precompute all pairs to compare
    pairs = []
    for idx, base in enumerate(folders):
        base_subs = get_level2_folders(base)
        base_hashes = {os.path.relpath(f, base): folder_hash(f) for f in base_subs}
        for jdx, other in enumerate(folders):
            if idx == jdx:
                continue
            other_subs = get_level2_folders(other)
            other_hashes = {os.path.relpath(f, other): folder_hash(f) for f in other_subs}
            for rel in set(base_hashes) & set(other_hashes):
                pairs.append((base, os.path.join(base, rel), other, os.path.join(other, rel), base_hashes[rel], other_hashes[rel]))
    PAGE_SIZE = 1000
    page = 0
    while True:
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        total = len(pairs)
        print(f"Total folder pairs to compare: {total}")
        if total > PAGE_SIZE:
            print(f"Showing page {page+1} ({start+1}-{min(end,total)}) of {total}")
        with open('equal_folders.txt', 'w') as out, open('equal_folders_deepcheck.txt', 'w') as deep:
            for i, (base, base_path, other, other_path, hash1, hash2) in enumerate(pairs[start:end], start+1):
                print(f"[{i}/{total}] Comparing:\n  {base_path}\n  {other_path}")
                if hash1 == hash2:
                    out.write(base + '\n' + base_path + '\n')
                    out.write(other + '\n' + other_path + '\n\n')
                    # Deep check
                    deep.write(f"== Deep check for ==\n{base_path}\n{other_path}\n")
                    folder_deep_compare(base_path, other_path, deep)
        if total <= PAGE_SIZE:
            break
        resp = input("Show next page of results? (y/N): ").strip().lower()
        if resp == 'y':
            page += 1
        else:
            break
    print("Comparison complete. Results in equal_folders.txt and deep details in equal_folders_deepcheck.txt")

if __name__ == "__main__":
    main()
