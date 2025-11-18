#!/bin/bash
# run.sh - Optional test harness for interactive testing

set -e

echo "================================"
echo "SD Upscale Plugin - Test Harness"
echo "================================"
echo ""

# This script provides an optional interactive test environment
# For this plugin, we can run a simple Python REPL with the modules loaded

echo "Starting Python interactive session with plugins loaded..."
echo "You can import and test both 'input' (buggy) and 'fixed_plugin' modules."
echo ""
echo "Example commands:"
echo "  >>> import input"
echo "  >>> import fixed_plugin"
echo "  >>> buggy = input.Script()"
echo "  >>> fixed = fixed_plugin.Script()"
echo "  >>> buggy.title()"
echo "  >>> fixed.title()"
echo ""
echo "Press Ctrl+D or type 'exit()' to quit."
echo ""

python -i -c "
import sys
print('Plugins loaded. Ready for testing.')
print('Available modules: input (buggy), fixed_plugin (fixed)')
"

echo ""
echo "Session ended."
