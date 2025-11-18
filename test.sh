#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
	echo "Please run ./setup.sh before testing."
	exit 1
fi

.venv/bin/python -m pytest tests
