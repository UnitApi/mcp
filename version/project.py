#!/usr/bin/env python3
"""
A script to increment the version in __init__.py file using semantic versioning.
"""
import re
import argparse
import os
import sys


# Usage examples:
# Default: increment patch version (0.1.8 → 0.1.9)
# ./increment_init.py

# Increment minor version (0.1.8 → 0.2.0)
# ./increment_init.py -t minor

# Increment major version (0.1.8 → 1.0.0)
# ./increment_init.py -t major

# Create a prerelease (0.1.8 → 0.1.8-alpha.1)
# ./increment_init.py -t prealpha

# Specify a custom file path
# ./increment_init.py -f src/unitmcp/__init__.py


def get_version_from_file(file_path):
    """Extract the current version from pyproject.toml file."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Look for version = "x.y.z" pattern
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return None


def increment_version(current_version, increment_type="patch"):
    """
    Increment the version number according to semantic versioning.

    Args:
        current_version: The current version string (e.g., "0.1.8")
        increment_type: The part of the version to increment:
                       "major" (1.0.0), "minor" (0.2.0), or "patch" (0.1.9)

    Returns:
        The new incremented version string
    """
    if not current_version:
        return "0.1.0"  # Default starting version

    # Parse version components
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(-([a-zA-Z0-9.-]+))?(\+([a-zA-Z0-9.-]+))?$', current_version)
    if not match:
        raise ValueError(f"Invalid version format: {current_version}. Expected format: X.Y.Z[-prerelease][+build]")

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    prerelease = match.group(5) if match.group(4) else None
    build = match.group(7) if match.group(6) else None

    # Increment appropriate component
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
        prerelease = None  # Clear prerelease on major version bump
    elif increment_type == "minor":
        minor += 1
        patch = 0
        prerelease = None  # Clear prerelease on minor version bump
    elif increment_type == "patch":
        patch += 1
        prerelease = None  # Clear prerelease on patch version bump
    elif increment_type.startswith("pre"):
        # Handle prerelease versions
        if prerelease:
            # If it's already a prerelease, try to increment its number
            pre_parts = prerelease.split('.')
            if len(pre_parts) > 1 and pre_parts[-1].isdigit():
                pre_parts[-1] = str(int(pre_parts[-1]) + 1)
                prerelease = '.'.join(pre_parts)
            else:
                prerelease = f"{prerelease}.1"
        else:
            # Start a new prerelease version
            prerelease_type = increment_type[3:] or "alpha"  # Extract alpha/beta/rc or default to alpha
            prerelease = f"{prerelease_type}.1"
    else:
        raise ValueError(
            f"Invalid increment type: {increment_type}. Expected 'major', 'minor', 'patch', or 'pre[type]'")

    # Construct new version
    new_version = f"{major}.{minor}.{patch}"
    if prerelease:
        new_version += f"-{prerelease}"
    if build:
        new_version += f"+{build}"

    return new_version




def update_version_in_init(file_path, increment_type="patch", backup=True):
    """
    Update the version in __init__.py file.

    Args:
        file_path: Path to __init__.py file
        increment_type: The part of the version to increment
        backup: Whether to create a backup of the original file

    Returns:
        Tuple of (success boolean, message string, new version)
    """
    try:
        # Get current version
        current_version = get_version_from_file(file_path)
        if not current_version:
            return False, f"Could not find version in {file_path}", None

        # Increment version
        new_version = increment_version(current_version, increment_type)

        # Read file content
        with open(file_path, 'r') as file:
            content = file.read()

        # Create backup if requested
        if backup:
            backup_file = f"{file_path}.bak"
            with open(backup_file, 'w') as file:
                file.write(content)

        # Replace version in file
        pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
        replacement = r'\g<1>' + new_version + r'\g<3>'
        new_content = re.sub(pattern, replacement, content)

        # Write updated content back to file
        with open(file_path, 'w') as file:
            file.write(new_content)

        return True, f"Version in {os.path.basename(file_path)} updated from {current_version} to {new_version}", new_version

    except Exception as e:
        return False, f"Error updating version: {e}", None


def main():
    """Parse command line arguments and update version."""
    parser = argparse.ArgumentParser(description="Increment version in __init__.py file")

    parser.add_argument(
        "-t", "--type",
        choices=["major", "minor", "patch", "prealpha", "prebeta", "prerc"],
        default="patch",
        help="Version increment type (default: patch)"
    )

    parser.add_argument(
        "-f", "--file",
        help="Path to __init__.py file (if not specified, will search recursively)"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup of the original file"
    )

    args = parser.parse_args()

    file_name = "pyproject.toml"
    file_path = "./" + file_name
    current_version = get_version_from_file(file_path)
    updated_versions = []
    all_success = True

    # Update each file
    if file_path:
        success, message, new_version = update_version_in_init(
            file_path=file_path,
            increment_type=args.type,
            backup=not args.no_backup
        )

        # Print result
        if success:
            print(f"✅ {message}")
            updated_versions.append((file_path, new_version))
        else:
            print(f"❌ {message}")
            all_success = False

    # Summary if multiple files were updated
    if len(updated_versions) > 1:
        print("\nSummary of updates:")
        for file_path, version in updated_versions:
            print(f"  • {file_path}: {version}")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())


# python increment_init.py -f src/unitmcp/__init__.py
# python increment_setup.py
# python changelog.py