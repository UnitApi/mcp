import os

def find_big_files(root, min_size_mb=100):
    big_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(path)
                if size >= min_size_mb * 1024 * 1024:
                    big_files.append((path, size))
            except Exception:
                continue
    return sorted(big_files, key=lambda x: -x[1])

def main():
    root = input("Enter the directory to search for large files: ").strip()
    min_size = input("Minimum file size in MB [default 100]: ").strip()
    try:
        min_size = int(min_size)
    except Exception:
        min_size = 100
    if not os.path.isdir(root):
        print("Invalid path!")
        return
    big_files = find_big_files(root, min_size)
    if not big_files:
        print("No large files found.")
        return
    print("Found large files:")
    for i, (path, size) in enumerate(big_files, 1):
        print(f"{i}) {path} ({size//1024//1024} MB)")
    resp = input("Enter file numbers to delete (space-separated, Enter to skip): ").strip()
    if resp:
        nums = [int(x) for x in resp.split() if x.isdigit()]
        for n in nums:
            try:
                os.remove(big_files[n-1][0])
                print(f"Deleted: {big_files[n-1][0]}")
            except Exception as e:
                print(f"Error deleting {big_files[n-1][0]}: {e}")

if __name__ == "__main__":
    main()
