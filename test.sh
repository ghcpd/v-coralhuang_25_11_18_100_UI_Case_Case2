#!/bin/bash
# Test script - runs automated tests against the fixed plugin

set -e

echo "=========================================="
echo "Running SD Upscale Plugin Tests"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate || . venv/bin/activate
fi

# Check if required files exist
if [ ! -f "fixed_plugin.py" ]; then
    echo "Error: fixed_plugin.py not found"
    exit 1
fi

if [ ! -f "test_plugin.py" ]; then
    echo "Error: test_plugin.py not found"
    exit 1
fi

if [ ! -f "test_harness.py" ]; then
    echo "Error: test_harness.py not found"
    exit 1
fi

# Run the test suite
echo "Executing test suite..."
echo ""

python3 test_plugin.py

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "✓ All tests passed!"
    echo "=========================================="
else
    echo "=========================================="
    echo "✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
    echo "=========================================="
fi

exit $TEST_EXIT_CODE


