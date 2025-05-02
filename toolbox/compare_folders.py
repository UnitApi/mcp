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
            # Do not descend deeper
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
    # Compare common files
    for fname in cmp.common_files:
        f1 = os.path.join(folder1, fname)
        f2 = os.path.join(folder2, fname)
        if not filecmp.cmp(f1, f2, shallow=False):
            return False
    # Compare subfolders recursively (but only at this level)
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

    subfolders1 = get_subfolders(dir1, depth)
    subfolders2 = get_subfolders(dir2, depth)

    # Map: relpath -> abs path
    rel_to_abs1 = {os.path.relpath(f, dir1): f for f in subfolders1}
    rel_to_abs2 = {os.path.relpath(f, dir2): f for f in subfolders2}

    common = set(rel_to_abs1.keys()) & set(rel_to_abs2.keys())
    for rel in common:
        f1 = rel_to_abs1[rel]
        f2 = rel_to_abs2[rel]
        files1 = count_files(f1)
        files2 = count_files(f2)
        if folders_are_equal(f1, f2):
            print(f"Found identical subfolders: {f1} (files: {files1}) and {f2} (files: {files2})")
            resp = input(f"Do you want to delete subfolder {f2}? [y/N]: ").strip().lower()
            if resp == 'y':
                shutil.rmtree(f2)
                print(f"Deleted {f2}")
            else:
                print("Skipping deletion.")

if __name__ == "__main__":
    main()
