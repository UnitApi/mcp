# Toolbox – System Cleanup Utilities

This `toolbox` folder contains a set of simple, interactive utilities for cleaning up files and directories on your computer. Each tool is a separate Python script, launched from a central menu.

## How to run?

1. Go to the toolbox directory:
   ```bash
   cd toolbox
   ```
2. Launch the menu:
   ```bash
   python3 menu.py
   ```
3. Choose a tool from the list and follow the on-screen instructions.

## Available tools

- **menu.py** – interactive menu for launching utilities
- **clean_empty_dirs.py** – finds and deletes empty directories
- **find_big_files.py** – finds and allows deletion of large files
- **compare_folders.py** – compares two folders and finds identical subfolders
- **move_duplicate_folders.py** – moves duplicate subfolders to a chosen directory
- **media_deduplicate.py** – intelligently finds and moves duplicate media files

Each tool works interactively and suggests common folders for convenience.

## Requirements

- Python 3.x

## Extending

You can easily add your own tools – just add a new .py file and list it in menu.py.
