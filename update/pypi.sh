#!/bin/bash

# Ensure script fails on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting publication process...${NC}"

echo -e "${GREEN}push changes...${NC}"
bash update/git.sh

echo -e "${GREEN}Check if we're in a clean git state${NC}"
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}Error: Git working directory is not clean${NC}"
    echo "Please commit or stash your changes first"
    exit 1
fi

# Clean up previous builds
echo -e "${GREEN}Cleaning up previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/

# Install/upgrade build tools
echo -e "${GREEN}Upgrading build tools...${NC}"
python -m pip list | grep -E 'setuptools|wheel|build|twine'
#python -m pip install --upgrade pip build twine
## update build tools
pip install --upgrade pip setuptools wheel build twine

# Build the package
echo -e "${GREEN}Building package...${NC}"
python -m build

# Check the distribution
echo -e "${GREEN}Checking distribution...${NC}"
twine check dist/*

echo -e "${GREEN}Publishing to PyPI...${NC}"
twine upload dist/*

