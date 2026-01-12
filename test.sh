#!/bin/bash
# test.sh - Run automated tests for the SD upscale plugin

set -e

echo "================================"
echo "SD Upscale Plugin - Test Suite"
echo "================================"
echo ""

# Check if required files exist
if [ ! -f "input.py" ]; then
    echo "ERROR: input.py not found!"
    exit 1
fi

if [ ! -f "fixed_plugin.py" ]; then
    echo "ERROR: fixed_plugin.py not found!"
    exit 1
fi

if [ ! -f "test_plugin.py" ]; then
    echo "ERROR: test_plugin.py not found!"
    exit 1
fi

echo "Running test suite..."
echo ""

# Run the tests
python test_plugin.py

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "================================"
    echo "✓ ALL TESTS PASSED"
    echo "================================"
else
    echo "================================"
    echo "✗ TESTS FAILED"
    echo "================================"
fi

exit $TEST_RESULT
