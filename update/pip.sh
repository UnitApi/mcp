#!/bin/bash

# Activate your virtual environment
source venv/bin/activate

# Uninstall existing PyAutoGUI
pip uninstall -y pyautogui

# Reinstall with verbose output
pip install --no-cache-dir --verbose pyautogui

# Additional dependencies
pip install python3-xlib Xlib pyudev