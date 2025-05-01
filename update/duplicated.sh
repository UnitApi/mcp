#!/bin/bash

# Create a backup of the original requirements file
cp requirements.txt requirements.txt.backup

# Remove duplicates while preserving order
awk '!seen[$0]++' requirements.txt > requirements_unique.txt

# Replace the original file with the unique packages version
mv requirements_unique.txt requirements.txt

echo "Duplicate packages have been removed from requirements.txt"