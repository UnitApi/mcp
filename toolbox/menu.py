import os
import sys

TOOLS = [
    ("Find and delete empty directories", "clean_empty_dirs.py"),
    ("Find and delete large files", "find_big_files.py"),
    ("Compare folders (identical subfolders)", "compare_folders.py"),
    ("Move duplicate subfolders", "move_duplicate_folders.py"),
    ("Media deduplication (intelligent)", "media_deduplicate.py"),
]

def suggest_dirs():
    home = os.path.expanduser("~")
    suggestions = [home, os.path.join(home, "Documents"), os.path.join(home, "Downloads"), os.path.join(home, "Pictures")]
    print("Example directories:")
    for s in suggestions:
        print(f"- {s}")

def main():
    print("=== SYSTEM CLEANUP TOOLBOX MENU ===")
    for i, (desc, _) in enumerate(TOOLS, 1):
        print(f"{i}) {desc}")
    print("0) Exit")
    try:
        choice = int(input("Select a tool: "))
    except Exception:
        print("Invalid choice!")
        return
    if choice == 0:
        print("Goodbye.")
        return
    if not (1 <= choice <= len(TOOLS)):
        print("Invalid choice!")
        return
    script = TOOLS[choice-1][1]
    script_path = os.path.join(os.path.dirname(__file__), script)
    if not os.path.exists(script_path):
        print(f"Tool file not found: {script_path}")
        return
    print("--- Directory suggestions ---")
    suggest_dirs()
    print("--- Launching tool ---")
    os.system(f"python3 {script_path}")

if __name__ == "__main__":
    main()
