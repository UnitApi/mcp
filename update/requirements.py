import re
import subprocess
import shutil
import sys
import logging


def clean_requirement(req):
    """
    Clean and validate requirement lines
    - Remove comments
    - Remove version constraints
    - Skip section headers
    """
    # Remove comments
    req = req.split('#')[0].strip()

    # Skip empty lines or section headers
    if not req or req.startswith('-'):
        return None

    # Remove version constraints
    cleaned_req = re.sub(r'[=<>]=?[0-9.]+', '', req).strip()

    return cleaned_req if cleaned_req else None


def update_requirements():
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Create a backup of the original requirements file
    shutil.copy('requirements.txt', 'requirements.txt.backup')
    logger.info("Created backup of requirements.txt")

    # Read the original requirements file
    with open('requirements.txt', 'r') as f:
        requirements = f.readlines()

    # Clean and filter requirements
    cleaned_requirements = []
    for req in requirements:
        cleaned_req = clean_requirement(req)
        if cleaned_req:
            cleaned_requirements.append(cleaned_req + '\n')

    # Write updated requirements
    with open('requirements.txt', 'w') as f:
        f.writelines(cleaned_requirements)
    logger.info("Removed version constraints and comments")

    # Upgrade pip
    try:
        subprocess.run(['pip', 'install', '--upgrade', 'pip'],
                       check=True,
                       capture_output=True,
                       text=True)
        logger.info("Pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e.stderr}")

    # Prepare to track failed packages
    failed_packages = []

    # Upgrade packages one by one to isolate problematic packages
    for package in cleaned_requirements:
        package = package.strip()
        if not package:
            continue

        try:
            # For platform-specific packages, use appropriate install command
            if ';' in package:
                base_package = package.split(';')[0].strip()
                result = subprocess.run(['pip', 'install', '--upgrade'] + package.split(),
                                        check=True,
                                        capture_output=True,
                                        text=True)
            else:
                result = subprocess.run(['pip', 'install', '--upgrade', package],
                                        check=True,
                                        capture_output=True,
                                        text=True)
            logger.info(f"Successfully upgraded {package}")

        except subprocess.CalledProcessError as e:
            # Special handling for PyAudio and other compilation-heavy packages
            if 'pyaudio' in package.lower():
                logger.warning(
                    "PyAudio requires additional system dependencies. Please install portaudio development libraries.")
                logger.warning("On Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio")
                logger.warning("On Fedora: sudo dnf install portaudio-devel python3-pyaudio")
                logger.warning("On macOS: brew install portaudio")

            logger.warning(f"Failed to upgrade {package}: {e.stderr}")
            failed_packages.append(package)

    # Print summary
    if failed_packages:
        logger.error("The following packages failed to upgrade:")
        for pkg in failed_packages:
            logger.error(pkg)

        # Write failed packages to a separate file
        with open('failed_upgrades.txt', 'w') as f:
            f.writelines(pkg + '\n' for pkg in failed_packages)

        logger.info("Failed packages have been written to failed_upgrades.txt")

        # Return a list of failed packages for potential further processing
        return failed_packages
    else:
        logger.info("All packages upgraded successfully")
        return []


if __name__ == '__main__':
    failed = update_requirements()
    sys.exit(1 if failed else 0)