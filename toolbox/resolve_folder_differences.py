import os
import shutil
import hashlib
import datetime
import fnmatch
import sys

# ANSI color helpers
RESET = '\033[0m'
BOLD = '\033[1m'
CYAN = '\033[36m'
YELLOW = '\033[33m'
RED = '\033[31m'
GREEN = '\033[32m'
MAGENTA = '\033[35m'
GRAY = '\033[90m'

def color(val, c):
    return f"{c}{val}{RESET}"

def get_levelN_folders(path, depth, ignore_patterns=None):
    folders = []
    for root, dirs, files in os.walk(path):
        rel = os.path.relpath(root, path)
        if rel == ".":
            cur_depth = 0
        else:
            cur_depth = rel.count(os.sep) + 1
        # Remove ignored dirs in-place
        dirs[:] = [d for d in dirs if not should_ignore(d, ignore_patterns or [])]
        if cur_depth == depth:
            if not should_ignore(os.path.basename(root), ignore_patterns or []):
                folders.append(root)
            dirs[:] = []
        elif cur_depth > depth:
            dirs[:] = []
    return folders

def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None
    except Exception:
        return None

def collect_files(folder, ignore_patterns=None):
    files = {}
    for root, dirs, fs in os.walk(folder):
        # Remove ignored dirs in-place
        dirs[:] = [d for d in dirs if not should_ignore(d, ignore_patterns or [])]
        for f in fs:
            if should_ignore(f, ignore_patterns or []):
                continue
            rel = os.path.relpath(os.path.join(root, f), folder)
            h = file_hash(os.path.join(root, f))
            if h is not None:
                files[rel] = h
    return files

def get_file_mtime(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ''

def load_ignore_patterns(ignore_path):
    patterns = []
    if not os.path.exists(ignore_path):
        with open(ignore_path, 'w') as f:
            f.write('.git\n')
        patterns = ['.git']
    else:
        with open(ignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def should_ignore(path, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or path.split(os.sep)[0] == pat:
            return True
    return False

def prompt_action_group(rel, folders, files_map):
    print(f"\n{BOLD}{CYAN}=== Difference detected for subfolder: {rel}{RESET}")
    col_headers = [f if f != '(missing)' else color('(missing)', GRAY) for f in folders]
    # Collect all files across all folders
    all_files = set()
    for fmap in files_map:
        all_files.update(fmap.keys())
    # Collect only files with differences, and sort to preserve structure
    diff_files = []
    for f in all_files:
        hashes = [fm.get(f) for fm in files_map]
        vals_present = [v for v in hashes if v is not None]
        if len(set(vals_present)) > 1 or hashes.count(None) > 0:
            diff_files.append(f)
    diff_files = sorted(diff_files, key=lambda x: (os.path.dirname(x), x))
    if not diff_files:
        print(color("No differences found in this subfolder.", GREEN))
        return 0, 0, 0
    maxlen = max([len(f) for f in diff_files] + [8, len('File')]) + 4
    col_width = max(27, max(len(h) for h in col_headers) + 2)
    # Build table
    header = f"{BOLD}{'File':<{maxlen}}{RESET} | " + " | ".join(f"{BOLD}{c:<{col_width}}{RESET}" for c in col_headers)
    print(header)
    print(color('-' * (maxlen + 3 + (col_width+3)*len(col_headers)), GRAY))
    # Each cell: show mtime if file exists, else blank
    for f in diff_files:
        row = [f"{f:<{maxlen}}"]
        for idx, fm in enumerate(files_map):
            abs_folder = folders[idx] if folders[idx] != '(missing)' else None
            abs_path = os.path.join(abs_folder, f) if abs_folder and fm.get(f) is not None else None
            if fm.get(f) is None:
                row.append(color('', GRAY))
            else:
                mtime = get_file_mtime(abs_path)
                mtimes = [get_file_mtime(os.path.join(folders[i], f)) if files_map[i].get(f) is not None and folders[i] != '(missing)' else None for i in range(len(folders))]
                valid = [t for t in mtimes if t]
                if mtime and valid:
                    if mtime == max(valid):
                        row.append(color(mtime, GREEN))
                    elif mtime == min(valid):
                        row.append(color(mtime, YELLOW))
                    else:
                        row.append(mtime)
                else:
                    row.append(mtime)
        print(" | ".join(f"{c:<{col_width}}" for c in row))
    print()
    # Dynamic menu
    print(color("What do you want to do?", MAGENTA))
    for i, f in enumerate(folders, 1):
        print(f"{CYAN}{i} - Delete: {f}{RESET}")
    for i, f in enumerate(folders, 1):
        for j, t in enumerate(folders, 1):
            if i != j:
                print(f"{YELLOW}{len(folders)+((i-1)*(len(folders)-1))+j-(1 if j>i else 0)} - Move {f} to 'different' in {t}, then delete {f}{RESET}")
    skip_opt = len(folders) + (len(folders)*(len(folders)-1)) + 1
    exit_opt = skip_opt + 1
    print(f"{MAGENTA}{skip_opt} - Skip{RESET}")
    print(f"{RED}{exit_opt} - Exit{RESET}")
    valid_choices = [str(i) for i in range(1, exit_opt+1)]
    while True:
        choice = input(f"Enter your choice [1-{exit_opt}]: ").strip()
        if choice in valid_choices:
            return int(choice), skip_opt, exit_opt

def move_and_delete(src, dst_root):
    dst = os.path.join(dst_root, 'different', os.path.basename(src))
    if os.path.exists(dst):
        print(f"Destination {dst} already exists! Skipping move.")
        return
    shutil.move(src, dst)
    print(f"Moved {src} -> {dst}")
    shutil.rmtree(src, ignore_errors=True)
    print(f"Deleted {src}")

def print_progress(current, total, prefix=''):
    bar_len = 40
    filled_len = int(round(bar_len * current / float(total))) if total else 0
    percents = round(100.0 * current / float(total), 1) if total else 100.0
    bar = color('=' * filled_len, GREEN) + color('-' * (bar_len - filled_len), GRAY)
    sys.stdout.write(f'\r{CYAN}{prefix}{RESET}[{bar}] {current}/{total} {percents}%')
    sys.stdout.flush()
    if current == total:
        print()

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
        print("Need at least two folders to compare.")
        return
    print("Folders to be compared:")
    for f in folders:
        print(f"  {f}")
    # Ask for depth
    try:
        depth = int(input(f"How deep should be scanned? (default 2): ").strip() or 2)
    except ValueError:
        depth = 2
    print(f"Scanning subfolders (level {depth}) in all input folders...")
    ignore_path = os.path.join(os.path.dirname(__file__), '.ignore')
    ignore_patterns = load_ignore_patterns(ignore_path)
    # Collect relpaths for all levelN subfolders
    all_rels = set()
    folder_subs = []
    for idx, f in enumerate(folders, 1):
        subs = get_levelN_folders(f, depth, ignore_patterns)
        rels = [os.path.relpath(s, f) for s in subs]
        folder_subs.append(dict(zip(rels, subs)))
        all_rels.update(rels)
        print_progress(idx, len(folders), prefix='Folders: ')
    print()
    all_rels = sorted(all_rels)
    any_menu = False
    for ridx, rel in enumerate(all_rels, 1):
        present = [fs.get(rel) for fs in folder_subs]
        if sum(x is not None for x in present) < 2:
            continue  # only in one folder
        # For each folder, collect files for this relpath
        files_map = []
        abs_paths = []
        print_progress(ridx, len(all_rels), prefix='Comparing: ')
        for idx, fs in enumerate(folder_subs):
            if rel in fs:
                abs_paths.append(fs[rel])
                files_map.append(collect_files(fs[rel], ignore_patterns))
            else:
                abs_paths.append(None)
                files_map.append({})
        # If all present and all files identical, skip
        all_files = set()
        for fm in files_map:
            all_files.update(fm.keys())
        skip = True
        for f in all_files:
            vals = [fm.get(f) for fm in files_map]
            vals_present = [v for v in vals if v is not None]
            if len(set(vals_present)) > 1:
                skip = False
                break
        if skip:
            continue
        # Show prompt and table, get choice
        choice, skip_opt, exit_opt = prompt_action_group(rel, [fs[rel] if rel in fs else '(missing)' for fs in folder_subs], files_map)
        if choice == exit_opt:
            print("Exiting.")
            return
        elif choice == skip_opt:
            print("Skipped.")
            continue
        any_menu = True
        # Delete or move+delete
        nfolders = len(folders)
        if 1 <= choice <= nfolders:
            tgt = [fs[rel] for fs in folder_subs][choice-1]
            if tgt and os.path.exists(tgt):
                shutil.rmtree(tgt)
                print(f"Deleted {tgt}")
        else:
            # Move+delete
            idx = (choice-nfolders-1) // (nfolders-1)
            jdx = (choice-nfolders-1) % (nfolders-1)
            src_idx = idx
            tgt_idx = jdx if jdx < idx else jdx+1
            src = [fs[rel] for fs in folder_subs][src_idx]
            tgt = [fs[rel] for fs in folder_subs][tgt_idx]
            if src and tgt and os.path.exists(src):
                move_and_delete(src, os.path.dirname(tgt))
    print_progress(len(all_rels), len(all_rels), prefix='Comparing: ')
    if not any_menu:
        print(color("No differences found between compared folders!", GREEN))
        # Ask for deletion of each folder
        for i, f in enumerate(folders, 1):
            ans = input(f"Do you want to delete folder {color(f, CYAN)}? [y/N]: ").strip().lower()
            if ans == 'y':
                try:
                    shutil.rmtree(f)
                    print(color(f"Deleted {f}", RED))
                except Exception as e:
                    print(color(f"Failed to delete {f}: {e}", RED))
    print("Done.")

if __name__ == "__main__":
    main()
