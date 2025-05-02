#!/usr/bin/env python3
"""
Hello World Example

This is a simple example to test if the start.py script works.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

RPI_HOST = os.getenv('RPI_HOST', 'localhost')
RPI_USERNAME = os.getenv('RPI_USERNAME', 'pi')


def main():
    """
    Main function that prints a hello world message.
    """
    print(f"Hello, World! This is a test example. Connecting to host {RPI_HOST} as {RPI_USERNAME}.")
    print("If you see this message in the correct/ directory, the example is working.")
    return 0

if __name__ == "__main__":
    main()
