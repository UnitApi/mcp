#!/usr/bin/env python3

import os
import platform
import subprocess
import sys
import sysconfig


def check_gcc():
    """Check GCC installation and version"""
    print("\n=== GCC Check ===")
    gcc_versions = ['gcc', 'gcc-11', 'gcc-10', 'gcc-9']

    for version in gcc_versions:
        try:
            result = subprocess.run([version, '--version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5)
            print(f"{version} version:")
            print(result.stdout.split('\n')[0])
            return version
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print("No suitable GCC version found.")
    return None


def check_python_config():
    """Check Python configuration details"""
    print("\n=== Python Configuration ===")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Executable: {sys.executable}")

    # Python include directories
    print("\nPython Include Directories:")
    include_dirs = [
        sysconfig.get_path('include'),
        sysconfig.get_path('platinclude')
    ]
    for inc_dir in include_dirs:
        print(f"  {inc_dir}")
        if os.path.exists(inc_dir):
            print("    Directory exists ✓")
        else:
            print("    Directory does not exist ✗")


def check_portaudio():
    """Check PortAudio installation"""
    print("\n=== PortAudio Check ===")

    # Potential library locations
    lib_locations = [
        '/usr/local/lib',
        '/usr/lib',
        '/usr/lib64',
        '/home/linuxbrew/.linuxbrew/lib'
    ]

    portaudio_libs = [
        'libportaudio.so',
        'libportaudio.so.2',
        'libportaudio.dylib',
        'libportaudio.a'
    ]

    found_libs = []
    for loc in lib_locations:
        for lib in portaudio_libs:
            full_path = os.path.join(loc, lib)
            if os.path.exists(full_path):
                found_libs.append(full_path)
                print(f"Found PortAudio library: {full_path}")

    if not found_libs:
        print("No PortAudio libraries found.")
        print("\nInstallation suggestions:")
        distro = platform.linux_distribution()[0] if platform.system() == 'Linux' else 'unknown'

        if 'Ubuntu' in distro or 'Debian' in distro:
            print("For Ubuntu/Debian:")
            print("  sudo apt-get update")
            print("  sudo apt-get install portaudio19-dev")
        elif 'Fedora' in distro:
            print("For Fedora:")
            print("  sudo dnf install portaudio-devel")
        else:
            print("Please install PortAudio development libraries for your distribution.")


def pip_check():
    """Check pip installation and environment"""
    print("\n=== Pip Check ===")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                                capture_output=True,
                                text=True)
        print(result.stdout.strip())
    except Exception as e:
        print(f"Pip check failed: {e}")


def main():
    print("=== PyAudio System Diagnostic ===")

    # Gather system information
    check_gcc()
    check_python_config()
    check_portaudio()
    pip_check()


if __name__ == '__main__':
    main()