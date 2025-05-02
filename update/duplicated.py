import shutil


def remove_duplicates_from_requirements():
    # Create a backup of the original requirements file
    shutil.copy('requirements.txt', 'requirements.txt.backup')

    # Read the original requirements file
    with open('requirements.txt', 'r') as f:
        requirements = f.readlines()

    # Remove duplicates while preserving order
    unique_requirements = []
    seen = set()
    for req in requirements:
        cleaned_req = req.strip()
        # Normalize the package name (lowercase, remove version specifiers)
        package_name = cleaned_req.split('==')[0].split('>=')[0].split('<=')[0].lower()

        if package_name not in seen and cleaned_req:
            seen.add(package_name)
            unique_requirements.append(cleaned_req + '\n')

    # Write unique requirements back to the file
    with open('requirements.txt', 'w') as f:
        f.writelines(unique_requirements)

    print(f"Removed {len(requirements) - len(unique_requirements)} duplicate packages.")
    print("Unique packages have been written to requirements.txt")


if __name__ == '__main__':
    remove_duplicates_from_requirements()