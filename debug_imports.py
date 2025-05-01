import sys
import os

print("Python Path:")
for path in sys.path:
    print(path)

print("\nTrying to find unitmcp package:")
try:
    import unitmcp
    print(f"unitmcp package found at: {unitmcp.__file__}")
    try:
        import unitmcp.core
        print(f"unitmcp.core found at: {unitmcp.core.__file__}")
    except ImportError as e:
        print(f"Failed to import unitmcp.core: {e}")
except ImportError as e:
    print(f"Failed to import unitmcp: {e}")

print("\nChecking if src/unitmcp/core exists:")
core_path = os.path.join(os.getcwd(), 'src', 'unitmcp', 'core')
print(f"Looking for: {core_path}")
print(f"Directory exists: {os.path.exists(core_path)}")
if os.path.exists(core_path):
    print("Contents:")
    print(os.listdir(core_path))
