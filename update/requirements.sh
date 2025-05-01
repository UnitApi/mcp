#!/bin/bash

# Remove version constraints and upgrade packages in requirements.txt

# Create a backup of the original requirements file
cp requirements.txt requirements.txt.backup

# Remove version constraints (==, >=, <=, etc.) and create a new requirements file
sed -E 's/[=<>]=?[0-9.]+//g' requirements.txt > requirements_updated.txt

# Upgrade pip first
pip install --upgrade pip

# Upgrade all packages in the updated requirements file
pip install --upgrade -r requirements_updated.txt

# Optional: Replace the original requirements file with the updated one
mv requirements_updated.txt requirements.txt

echo "Packages have been updated and version constraints removed."