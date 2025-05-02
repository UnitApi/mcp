#!/bin/bash

# Run tests
echo "Running tests..."
pytest tests/ || { echo "Tests failed"; exit 1; }

# Check code style
echo "Checking code style..."
black --check src/ examples/ tests/
isort --check-only src/ examples/ tests/
flake8 src/ examples/ tests/
tox -e py312

#tox -e py312 -- tests/test_server.py::TestMCPHardwareServer::test_handle_client_request -v
# python -m pytest tests/test_server.py::TestMCPHardwareServer::test_handle_client_request -v --no-header --tb=native --cov=unitmcp --cov-report=term-missing