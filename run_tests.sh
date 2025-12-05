#!/bin/bash
# Script to run Ygam tests

set -e

echo "======================================"
echo "     Ygam Test Suite Runner"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install test dependencies
echo ""
echo "Installing test dependencies..."
pip install -q -r requirements-test.txt

# Run tests based on argument
echo ""
echo "======================================"
echo "Running tests..."
echo "======================================"
echo ""

if [ "$1" == "coverage" ]; then
    echo "Running with coverage report..."
    pytest --cov=. --cov-report=html --cov-report=term
    echo ""
    echo "✅ Coverage report generated in htmlcov/index.html"
elif [ "$1" == "verbose" ]; then
    echo "Running in verbose mode..."
    pytest -v
elif [ "$1" == "fast" ]; then
    echo "Running fast tests only (skipping slow)..."
    pytest -m "not slow"
elif [ "$1" == "auth" ]; then
    echo "Running authentication tests only..."
    pytest tests/test_auth.py -v
elif [ "$1" == "models" ]; then
    echo "Running model tests only..."
    pytest tests/test_models.py -v
elif [ "$1" == "middleware" ]; then
    echo "Running middleware tests only..."
    pytest tests/test_middleware.py -v
elif [ "$1" == "utils" ]; then
    echo "Running utils tests only..."
    pytest tests/test_utils.py -v
else
    echo "Running all tests..."
    pytest
fi

echo ""
echo "======================================"
echo "✅ Tests completed!"
echo "======================================"
