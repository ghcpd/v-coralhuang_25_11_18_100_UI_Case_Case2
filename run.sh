#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
	echo "Please run ./setup.sh before using run.sh."
	exit 1
fi

.venv/bin/python fixed_plugin.py
