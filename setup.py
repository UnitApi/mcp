#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Installation of the unitmcp package.
"""

import os
from setuptools import setup, find_packages

# Long description from README.md
try:
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ''

# Get version from _version.py
version = {}
with open("src/unitmcp/_version.py") as f:
    exec(f.read(), version)

# Fallback if _version.py is missing or empty
if not version.get("__version__"):
    version["__version__"] = "0.1.0"

# Configuration setup
setup(
    name="unitmcp",
    version=version["__version__"],
    description="UnitMCP package for MCP hardware integration with Ollama LLM and Raspberry Pi hardware control.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    maintainer="unitmcp developers",
    maintainer_email="info@softreck.dev",
    python_requires=">=3.7.3",
    url="https://unitmcp.unitapi.com",
    install_requires=[
        # Core dependencies
        "pyyaml>=6.0.1",
        "psutil>=5.9.0",
        "requests>=2.31.0",
        "urllib3>=1.26.9",
        "websockets>=10.3",
        "aiohttp>=3.8.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.27.0",
        "acme>=4.0.0",
        "cryptography>=42.0.0",
        "certbot>=2.7.0",
        "dnspython>=2.4.0",
        "upnpclient>=1.0.3",
        "zeroconf>=0.38.1",
        "wsdiscovery>=2.0.0",
        "onvif-zeep>=0.2.12",
        "opencv-python>=4.5.0",
        "pillow>=11.2.0",
        "pyautogui>=0.9.50",
        "pynput>=1.7.0",
        "pyaudio>=0.2.11",
        "sounddevice>=0.4.0",
        "paramiko>=3.5.1",
        "numpy>=1.22.3",
        "grpcio>=1.62.0",
        "grpcio-tools>=1.62.0",
        "paho-mqtt>=1.6.0",
        "redis>=4.0.0",
        "pydantic>=1.9.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            # Testing
            "pytest>=8.3.5",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.23.0",
            "pytest-mock>=3.12.0",
            
            # Code quality
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            
            # Type checking
            "types-requests>=2.31.0",
            "types-PyYAML>=6.0.1",
            "types-psutil>=5.9.0",
            "python-dotenv>=1.1.0",
        ],
        "dsl": [
            # DSL format support
            "python-hcl2>=3.0.5",
            "starlark>=0.4.0",
        ],
        "audio": [
            # Audio processing dependencies
            "pyaudio>=0.2.11",
            "sounddevice>=0.4.0",
            "soundfile>=0.12.1",
        ],
    },
    project_urls={
        "Repository": "https://github.com/unitmcp/python",
        "Changelog": "https://github.com/unitmcp/python/releases",
        "Wiki": "https://github.com/unitmcp/python/wiki",
        "Issue Tracker": "https://github.com/unitmcp/python/issues/new",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'unitmcp=unitmcp.main:main',
            'unitmcp-dsl=unitmcp.cli:main',
        ],
    },
    license="Apache-2.0",
    license_files=("LICENSE",),
    keywords=["python", "unitmcp", "streaming", "real-time", "annotation", "processing"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Multimedia :: Video',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
