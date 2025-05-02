#!/usr/bin/env python3

import subprocess
import sys
import platform
import os


def run_pip_command(command, **kwargs):
    """
    Run pip command with --break-system-packages flag
    """
    full_command = [sys.executable, '-m', 'pip'] + command + ['--break-system-packages']
    return subprocess.run(full_command, **kwargs)


def install_pyaudio():
    """
    Attempt to install PyAudio with multiple methods
    specifically tailored for Homebrew Python
    """
    # Paths for Homebrew Python
    homebrew_python_base = os.path.dirname(os.path.dirname(sys.executable))
    include_path = os.path.join(homebrew_python_base, 'include',
                                f'python{sys.version_info.major}.{sys.version_info.minor}')
    lib_path = os.path.join(homebrew_python_base, 'lib')

    # Installation methods
    install_methods = [
        # Standard pip install with system packages broken
        ['install', 'pyaudio'],

        # No binary installation
        ['install', '--no-binary', ':all:', 'pyaudio'],

        # Specific compilation flags
        ['install', 'pyaudio',
         f'--global-option=build_ext',
         f'--global-option=-I{include_path}',
         f'--global-option=-L{lib_path}'],

        # Force reinstall with specific Python include path
        ['install',
         '--force-reinstall',
         '--no-use-pep517',
         f'--global-option=build_ext',
         f'--global-option=-I{include_path}',
         f'--global-option=-L{lib_path}',
         'pyaudio']
    ]

    # Try each installation method
    for method in install_methods:
        try:
            print(f"\nAttempting installation with method: pip {' '.join(method)}")
            result = run_pip_command(method,
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
    print("PyAudio Installation for Homebrew Python")
    print("======================================")

    # System information
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {sys.executable}")
    print(f"System: {platform.system()}")
    print(f"Release: {platform.release()}")

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