#!/bin/bash

brew install python-tk
sudo dnf install python3-tkinter python3-devel
venv/bin/pip install --upgrade pip && venv/bin/pip install -r requirements.txt
which python3  # Upewnij się, że to /usr/bin/python3, nie /home/linuxbrew/...
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
python -m tox