# Installation Guide for UnitMCP

This directory contains scripts to help you install the necessary dependencies for UnitMCP, including tkinter which is required for some GUI-related functionality.

## Tkinter Installation

Tkinter is a Python binding to the Tk GUI toolkit and is required for certain features in UnitMCP, particularly those that use PyAutoGUI for screen capture and mouse/keyboard control.

### Linux

Run the following command to install tkinter and other dependencies:

```bash
# Make the script executable
chmod +x install_tkinter.sh

# Run the script
./install_tkinter.sh
```

The script will detect your Linux distribution and use the appropriate package manager to install tkinter.

### Windows

Run the PowerShell script to check your tkinter installation and install other dependencies:

```powershell
# Run the script
.\install_tkinter.ps1
```

If tkinter is not installed, the script will provide instructions for reinstalling Python with the tkinter option enabled.

### macOS

On macOS, tkinter should be included with Python. Run the bash script to verify:

```bash
# Make the script executable
chmod +x install_tkinter.sh

# Run the script
./install_tkinter.sh
```

## Manual Installation

If the scripts don't work for your system, you can manually install tkinter:

### Linux

- Debian/Ubuntu: `sudo apt-get install python3-tk python3-dev`
- Fedora: `sudo dnf install python3-tkinter`
- Arch Linux: `sudo pacman -S tk`
- openSUSE: `sudo zypper install python3-tk`

### Windows

On Windows, tkinter is included with Python. Make sure to check the "tcl/tk and IDLE" option during Python installation.

### macOS

On macOS, tkinter is included with Python. If you're using Homebrew, you can reinstall Python:

```bash
brew install python
```

## Testing Tkinter Installation

You can verify that tkinter is installed correctly by running:

```python
python -c "import tkinter; tkinter._test()"
```

This should open a small window with buttons and other widgets.

## Troubleshooting

If you encounter issues with tkinter:

1. Make sure you have the latest version of Python installed.
2. On Linux, ensure you have the development packages installed.
3. On Windows, reinstall Python and make sure to check the tkinter option.
4. On macOS, try reinstalling Python using Homebrew.

For more help, please refer to the [official tkinter documentation](https://docs.python.org/3/library/tkinter.html).
