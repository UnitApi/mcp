#!/bin/bash

brew install python-tk
brew install gcc@11
sudo dnf install python3-tkinter python3-devel
sudo dnf install gcc gcc-c++ python3-devel libxml2-devel libxslt-devel
sudo dnf install python3-tkinter python3-devel gcc gcc-c++ portaudio-devel libevdev-devel libxml2-devel libxslt-devel
export CC=gcc-11
venv/bin/pip install --upgrade pip && venv/bin/pip install -r requirements.txt
which python3  # Upewnij się, że to /usr/bin/python3, nie /home/linuxbrew/...
rm -rf venv
python -m venv venv

clear
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest
tox