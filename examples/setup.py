#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="unitmcp",
    version="0.1.0",
    description="Unit MCP Hardware Access Library",
    author="MCP Team",
    author_email="mcp@example.com",
    packages=find_packages(),
    install_requires=[
        "paho-mqtt",
        "pyaudio",
        "numpy",
        "pyyaml",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)
