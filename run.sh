#!/bin/bash
# Run script - starts any necessary local server or harness
# For this plugin, we don't need a server, but we can use this to verify setup

set -e

echo "Checking environment setup..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate || . venv/bin/activate
fi

# Check if Python can import required modules
echo "Verifying Python environment..."
python3 -c "import PIL; import gradio; print('✓ All dependencies available')" || {
    echo "Error: Missing dependencies. Run ./setup.sh first"
    exit 1
}

echo ""
echo "Environment is ready. Run ./test.sh to execute tests."


