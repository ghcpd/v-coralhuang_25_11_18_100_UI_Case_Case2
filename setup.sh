#!/bin/bash
# setup.sh - Install all required dependencies for the SD upscale plugin testing

set -e

echo "================================"
echo "SD Upscale Plugin - Setup Script"
echo "================================"
echo ""

# Check Python version
echo "Checking Python installation..."
python --version

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install required packages
echo ""
echo "Installing required Python packages..."
python -m pip install Pillow

# Verify installations
echo ""
echo "Verifying installations..."
python -c "import PIL; print(f'Pillow {PIL.__version__} installed successfully')"

echo ""
echo "================================"
echo "Setup completed successfully!"
echo "================================"
echo ""
echo "You can now run:"
echo "  ./test.sh      - Run the test suite"
echo "  ./run.sh       - Start the test harness (optional)"
