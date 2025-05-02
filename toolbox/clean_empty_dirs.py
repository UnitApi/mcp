import os

def find_empty_dirs(root):
    empty_dirs = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if not dirnames and not filenames:
            empty_dirs.append(dirpath)
    return empty_dirs

def main():
    root = input("Enter the directory to search for empty folders: ").strip()
    if not os.path.isdir(root):
        print("Invalid path!")
        return
    empty_dirs = find_empty_dirs(root)
    if not empty_dirs:
        print("No empty folders found.")
        return
    print("Found empty folders:")
    for d in empty_dirs:
        print(d)
    resp = input("Delete all these folders? [y/N]: ").strip().lower()
    if resp == 'y':
        for d in empty_dirs:
            try:
                os.rmdir(d)
                print(f"Deleted: {d}")
            except Exception as e:
                print(f"Error deleting {d}: {e}")

if __name__ == "__main__":
    main()
