#!/bin/bash
python3 -m pip install --upgrade pip setuptools wheel

if ldconfig -p | grep -q libportaudio; then
    echo -e "${GREEN}PortAudio library found ✓${NC}"
else
    echo -e "${RED}PortAudio library not found ✗${NC}"
    return 1
fi