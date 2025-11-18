#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
	python3 -m venv .venv
fi

if [ ! -f ".venv/bin/pip" ]; then
	tmpfile=$(mktemp)
	curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$tmpfile"
	.venv/bin/python "$tmpfile"
	rm "$tmpfile"
fi

.venv/bin/python -m pip install -r requirements.txt
