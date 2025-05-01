#!/bin/bash

echo "Publishing new version to GitHub..."

# Function to extract latest version from CHANGELOG.md
get_latest_version() {
    # Extract the first version number found in CHANGELOG.md
    version=$(grep -m 1 "## \[.*\]" CHANGELOG.md | grep -o "\[.*\]" | tr -d "[]")
    echo $version
}

# Function to extract latest changes from CHANGELOG.md
get_latest_changes() {
    # Read CHANGELOG.md and extract content between first and second version headers
    awk '/^## \[/{i++}i==1{print}i==2{exit}' CHANGELOG.md | tail -n +2
}

# Get version and changes
VERSION=$(get_latest_version)
if [ -z "$VERSION" ]; then
    echo "Error: Could not find version in CHANGELOG.md"
    exit 1
fi

echo "Found version: $VERSION"

# Store changes in a temporary file
TEMP_FILE=$(mktemp)
get_latest_changes > "$TEMP_FILE"

if [ ! -s "$TEMP_FILE" ]; then
    echo "Error: Could not extract changes from CHANGELOG.md"
    rm "$TEMP_FILE"
    exit 1
fi

echo -e "\nChanges to be published:"
cat "$TEMP_FILE"

# Confirm with user
#read -p "Continue with publish? (y/n) " -n 1 -r


# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    rm "$TEMP_FILE"
    exit 1
fi

# Add all changes
git add .

# Create commit with changelog entry
git commit -m "Release version $VERSION

$(cat "$TEMP_FILE")"

# Create and push tag
git tag -a "v$VERSION" -m "Version $VERSION

$(cat "$TEMP_FILE")"

# Push changes and tags
echo "Pushing changes and tags to GitHub..."
git push origin main
git push origin "v$VERSION"

# Cleanup
rm "$TEMP_FILE"

echo "Successfully published version $VERSION"
