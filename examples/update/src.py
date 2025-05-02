#!/usr/bin/env python3
"""
A script to update version in Python package files.
Supports different version declaration formats.
"""
import re
import argparse
import os
import sys


def get_version_from_file(file_path):
    """Extract the current version from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Try different version patterns
            patterns = [
                r'__version__\s*=\s*(?:version\s*=\s*)?[\'"]([^\'"]+)[\'"]',  # __version__ = version = "0.1.3"
                r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]',  # __version__ = "0.1.8"
                # Only match version = ... if not prefixed by python_
                r'(?<!python_)version\s*=\s*[\'"]([^\'"]+)[\'"]'  # version = "0.1.3" (not python_version)
            ]

            for pattern in patterns:
                version_match = re.search(pattern, content)
                if version_match:
                    return version_match.group(1), content

            print(f"Warning: No version pattern found in {file_path}")
            return None, content
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return None, None


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


def set_specific_version(new_version):
    """Validate that a manually specified version follows semantic versioning."""
    # Basic check for semantic versioning format
    if not re.match(r'^\d+\.\d+\.\d+(-([a-zA-Z0-9.-]+))?(\+([a-zA-Z0-9.-]+))?$', new_version):
        raise ValueError(f"Invalid version format: {new_version}. Expected format: X.Y.Z[-prerelease][+build]")
    return new_version


def update_version_in_file(file_path, new_version=None, increment_type="patch", backup=True):
    """
    Update the version in a Python file.

    Args:
        file_path: Path to the file
        new_version: Specific version to set (overrides increment_type if provided)
        increment_type: The part of the version to increment if new_version is not specified
        backup: Whether to create a backup of the original file

    Returns:
        Tuple of (success boolean, message string, new version)
    """
    try:
        # Get current version and content
        current_version, content = get_version_from_file(file_path)
        if not current_version or not content:
            return False, f"Could not find version in {file_path}", None

        # Determine new version
        if new_version:
            target_version = set_specific_version(new_version)
        else:
            target_version = increment_version(current_version, increment_type)

        # Create backup if requested
        if backup:
            backup_file = f"{file_path}.bak"
            with open(backup_file, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Backup created: {backup_file}")

        # Replace version in different formats
        patterns = [
            (r'(__version__\s*=\s*version\s*=\s*)[\'"]([^\'"]+)[\'"]', rf'\g<1>"{target_version}"'),
            (r'(__version__\s*=\s*)[\'"]([^\'"]+)[\'"]', rf'\g<1>"{target_version}"'),
            (r'(version\s*=\s*)[\'"]([^\'"]+)[\'"]', rf'\g<1>"{target_version}"')
        ]

        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content)

        # Write updated content back to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)

        return True, f"Version in {os.path.basename(file_path)} updated from {current_version} to {target_version}", target_version

    except Exception as e:
        return False, f"Error updating version: {e}", None


def main():
    """Parse command line arguments and update version."""
    parser = argparse.ArgumentParser(description="Update version in Python package files")

    parser.add_argument(
        "-f", "--file",
        required=True,
        help="Path to the Python file containing version information"
    )

    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "-t", "--type",
        choices=["major", "minor", "patch", "prealpha", "prebeta", "prerc"],
        default="patch",
        help="Version increment type (default: patch)"
    )
    version_group.add_argument(
        "-v", "--version",
        help="Set specific version (overrides --type)"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup of the original file"
    )

    args = parser.parse_args()

    success, message, new_version = update_version_in_file(
        file_path=args.file,
        new_version=args.version,
        increment_type=args.type,
        backup=not args.no_backup
    )

    if success:
        print(f"✅ {message}")
        return 0
    else:
        print(f"❌ {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())