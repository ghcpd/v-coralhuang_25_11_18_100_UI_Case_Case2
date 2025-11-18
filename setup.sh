#!/bin/bash
# Setup script for SD upscale plugin testing environment

set -e

echo "Setting up SD upscale plugin test environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install Pillow gradio

echo ""
echo "Setup complete!"
echo "To activate the environment, run: source venv/bin/activate"
echo "Or use: . venv/bin/activate"


