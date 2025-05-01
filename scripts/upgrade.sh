# Script to upgrade all development requirements to their latest versions

# Ensure we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate your virtual environment first."
    exit 1
fi

# Create a temporary file for the updated requirements
TMP_FILE=$(mktemp)

# Get current requirements without version constraints
grep -v "^#" requirements-dev.txt | sed 's/[<>=].*//' > "$TMP_FILE"

# Install the latest versions
pip install --upgrade -r "$TMP_FILE"

# Generate the new requirements file
pip freeze > requirements-dev.txt.new

# Keep only the packages that were in the original requirements-dev.txt
while IFS= read -r package; do
    # Skip empty lines and comments
    if [[ -z "$package" || "$package" == \#* ]]; then
        continue
    fi

    # Extract package name (remove version specifiers)
    pkg_name=$(echo "$package" | sed 's/[<>=].*//')

    # Find the package in the new requirements file
    grep -i "^$pkg_name==" requirements-dev.txt.new >> requirements-dev.txt.updated
done < requirements-dev.txt

# Replace the old file with the new one
mv requirements-dev.txt.updated requirements-dev.txt

# Clean up
rm "$TMP_FILE" requirements-dev.txt.new

echo "Development requirements have been upgraded to their latest versions."
