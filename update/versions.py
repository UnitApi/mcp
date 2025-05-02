#!/usr/bin/env python3

import sys
import re
import subprocess
from typing import Dict, List, Optional, Tuple


class RequirementsUpdater:
    def __init__(self, input_file: str = 'requirements.txt', output_file: str = 'requirements.txt'):
        """
        Initialize the RequirementsUpdater with input and output file paths.

        :param input_file: Path to the input requirements file
        :param output_file: Path to save the updated requirements file
        """
        self.input_file = input_file
        self.output_file = output_file
        self.requirements: List[str] = []
        self.platform = sys.platform
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    def read_requirements(self) -> None:
        """
        Read requirements from the input file.
        """
        try:
            with open(self.input_file, 'r') as f:
                self.requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"Error: File {self.input_file} not found.")
            sys.exit(1)

    def get_latest_version(self, package: str, platform_condition: Optional[str] = None) -> Optional[str]:
        """
        Get the latest version of a package using pip.

        :param package: Name of the package
        :param platform_condition: Optional platform-specific condition
        :return: Latest version string or None
        """
        try:
            # Remove version specifiers and platform conditions
            base_package = re.split(r'[=<>]', package)[0].split(';')[0].strip()

            # Check platform and version conditions
            if platform_condition:
                # Platform check
                if 'platform_system == "Windows"' in platform_condition and self.platform != 'win32':
                    return None
                if 'platform_system != "Windows"' in platform_condition and self.platform == 'win32':
                    return None

                # Python version check
                if 'python_version' in platform_condition:
                    if '<' in platform_condition:
                        version_limit = platform_condition.split('<')[1].strip('"')
                        if self.python_version >= version_limit:
                            return None
                    elif '>=' in platform_condition:
                        version_limit = platform_condition.split('>=')[1].strip('"')
                        if self.python_version < version_limit:
                            return None

            # Run pip command to get latest version
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'index', 'versions', base_package],
                capture_output=True,
                text=True,
                timeout=30  # Add timeout to prevent hanging
            )

            # Extract the latest version
            if result.returncode == 0:
                version_match = re.search(r'Available versions: (.+)', result.stdout)
                if version_match:
                    # Take the first (latest) version
                    latest_version = version_match.group(1).split(',')[0].strip()

                    # Reconstruct the requirement with the latest version
                    latest_req = f"{base_package}=={latest_version}"
                    if platform_condition:
                        latest_req += f"; {platform_condition}"

                    return latest_req
        except subprocess.TimeoutExpired:
            print(f"Timeout checking version for {base_package}")
        except Exception as e:
            print(f"Error checking version for {base_package}: {e}")

        return None

    def update_requirements(self) -> List[Tuple[str, Optional[str]]]:
        """
        Update requirements to their latest versions.

        :return: List of tuples with (original requirement, updated requirement)
        """
        updated_requirements = []

        for req in self.requirements:
            # Split platform conditions if present
            parts = req.split(';')
            package = parts[0].strip()
            platform_condition = parts[1].strip() if len(parts) > 1 else None

            # Get latest version
            latest_version = self.get_latest_version(package, platform_condition)

            # If latest version found, update
            if latest_version:
                updated_requirements.append((req, latest_version))
            else:
                # Keep original if no update found
                updated_requirements.append((req, None))

        return updated_requirements

    def write_requirements(self, updated_requirements: List[Tuple[str, Optional[str]]]) -> None:
        """
        Write updated requirements to the output file.

        :param updated_requirements: List of tuples with (original, updated) requirements
        """
        try:
            with open(self.output_file, 'w') as f:
                for original, updated in updated_requirements:
                    # Write updated version or original if no update found
                    if updated:
                        print(f"Updated: {original} -> {updated}")
                        f.write(f"{updated}\n")
                    else:
                        print(f"No update found for: {original}")
                        f.write(f"{original}\n")
        except IOError as e:
            print(f"Error writing to {self.output_file}: {e}")
            sys.exit(1)

    def run(self) -> None:
        """
        Run the entire requirements update process.
        """
        print("Starting requirements update...")

        # Read input requirements
        self.read_requirements()

        # Update requirements
        updated_requirements = self.update_requirements()

        # Write updated requirements
        self.write_requirements(updated_requirements)

        print("Requirements update completed.")


def main():
    """
    Main function to run the requirements updater.
    """
    try:
        # Create updater instance
        updater = RequirementsUpdater()

        # Run the update process
        updater.run()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
# !/usr/bin/env python3

import sys
import subprocess
import re
from typing import Dict, List, Optional, Tuple


class RequirementsUpdater:
    def __init__(self, input_file: str = 'requirements.txt', output_file: str = 'requirements.txt'):
        """
        Initialize the RequirementsUpdater with input and output file paths.

        :param input_file: Path to the input requirements file
        :param output_file: Path to save the updated requirements file
        """
        self.input_file = input_file
        self.output_file = output_file
        self.requirements: List[str] = []
        self.platform = sys.platform

    def read_requirements(self) -> None:
        """
        Read requirements from the input file.
        """
        try:
            with open(self.input_file, 'r') as f:
                self.requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"Error: File {self.input_file} not found.")
            sys.exit(1)

    def get_latest_version(self, package: str, platform_condition: Optional[str] = None) -> Optional[str]:
        """
        Get the latest version of a package using pip.

        :param package: Name of the package
        :param platform_condition: Optional platform-specific condition
        :return: Latest version string or None
        """
        # Remove platform-specific conditions for version check
        base_package = re.split(r';', package)[0].split('==')[0].strip()

        try:
            # Check platform and version conditions
            if platform_condition:
                # Evaluate platform condition
                if platform_condition == 'platform_system == "Windows"' and self.platform != 'win32':
                    return None
                if platform_condition == 'platform_system != "Windows"' and self.platform == 'win32':
                    return None
                if platform_condition.startswith('python_version'):
                    # Check Python version condition
                    import sys
                    if '<' in platform_condition:
                        version_check = platform_condition.split('<')[1].strip('"')
                        if sys.version_info >= tuple(map(int, version_check.split('.'))):
                            return None
                    elif '>=' in platform_condition:
                        version_check = platform_condition.split('>=')[1].strip('"')
                        if sys.version_info < tuple(map(int, version_check.split('.'))):
                            return None

            # Run pip command to get latest version
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'index', 'versions', base_package],
                capture_output=True,
                text=True
            )

            # Extract the latest version
            if result.returncode == 0:
                # Look for the first version line
                version_match = re.search(r'Available versions: (.+)', result.stdout)
                if version_match:
                    # Take the first (latest) version
                    latest_version = version_match.group(1).split(',')[0].strip()
                    return f"{base_package}=={latest_version}"
        except Exception as e:
            print(f"Error checking version for {base_package}: {e}")

        return None

    def update_requirements(self) -> List[Tuple[str, Optional[str]]]:
        """
        Update requirements to their latest versions.

        :return: List of tuples with (original requirement, updated requirement)
        """
        updated_requirements = []

        for req in self.requirements:
            # Split platform conditions if present
            parts = re.split(r';', req)
            package = parts[0].strip()
            platform_condition = parts[1] if len(parts) > 1 else None

            # Get latest version
            latest_version = self.get_latest_version(package, platform_condition)

            # If latest version found, update
            if latest_version:
                if platform_condition:
                    latest_version = f"{latest_version}; {platform_condition}"
                updated_requirements.append((req, latest_version))
            else:
                # Keep original if no update found
                updated_requirements.append((req, None))

        return updated_requirements

    def write_requirements(self, updated_requirements: List[Tuple[str, Optional[str]]]) -> None:
        """
        Write updated requirements to the output file.

        :param updated_requirements: List of tuples with (original, updated) requirements
        """
        try:
            with open(self.output_file, 'w') as f:
                for original, updated in updated_requirements:
                    # Write updated version or original if no update found
                    if updated:
                        print(f"Updated: {original} -> {updated}")
                        f.write(f"{updated}\n")
                    else:
                        print(f"No update found for: {original}")
                        f.write(f"{original}\n")
        except IOError as e:
            print(f"Error writing to {self.output_file}: {e}")
            sys.exit(1)

    def run(self) -> None:
        """
        Run the entire requirements update process.
        """
        print("Starting requirements update...")

        # Read input requirements
        self.read_requirements()

        # Update requirements
        updated_requirements = self.update_requirements()

        # Write updated requirements
        self.write_requirements(updated_requirements)

        print("Requirements update completed.")


def main():
    """
    Main function to run the requirements updater.
    """
    try:
        # Create updater instance
        updater = RequirementsUpdater()

        # Run the update process
        updater.run()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()