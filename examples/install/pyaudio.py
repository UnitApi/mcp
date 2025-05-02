#!/usr/bin/env python3

import subprocess
import sys
import platform


def install_pyaudio():
    """
    Attempt to install PyAudio with multiple methods
    specifically tailored for Fedora with Python 3.13
    """
    # Ensure pip and wheel are up to date
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'wheel'], check=True)

    # Installation methods
    install_methods = [
        # Standard pip install
        [sys.executable, '-m', 'pip', 'install', 'pyaudio'],

        # No binary installation
        [sys.executable, '-m', 'pip', 'install', '--no-binary', ':all:', 'pyaudio'],

        # Specific compilation flags
        [sys.executable, '-m', 'pip', 'install',
         'pyaudio',
         '--global-option=build_ext',
         '--global-option=-I/usr/include/python3.13'],

        # Force reinstall with specific Python include path
        [sys.executable, '-m', 'pip', 'install',
         '--force-reinstall',
         '--no-use-pep517',
         f'--global-option=build_ext',
         f'--global-option=-I/usr/include/python3.13',
         'pyaudio']
    ]

    # Try each installation method
    for method in install_methods:
        try:
            print(f"\nAttempting installation with method: {' '.join(method)}")
            result = subprocess.run(method,
                                    check=True,
                                    capture_output=True,
                                    text=True)
            print("Installation successful!")

            # Verify import
            subprocess.run([sys.executable, '-c', 'import pyaudio; print(pyaudio.__version__)'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation method failed. Error:\n{e.stderr}")

    return False


def main():
    print("PyAudio Installation for Fedora")
    print("==============================")

    # System information
    print(f"Python Version: {platform.python_version()}")
    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")

    # Verify system prerequisites
    try:
        # Check for required development packages
        subprocess.run(['rpm', '-q', 'python3-devel', 'portaudio-devel'], check=True)
        print("\nRequired development packages are installed.")
    except subprocess.CalledProcessError:
        print("\nWARNING: Some required development packages might be missing.")
        print("Recommended installation:")
        print("sudo dnf install python3-devel portaudio-devel")
        return False

    # Attempt PyAudio installation
    if install_pyaudio():
        print("\n✓ PyAudio installed successfully!")
        return True
    else:
        print("\n✗ PyAudio installation failed.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)