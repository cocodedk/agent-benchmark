#!/usr/bin/env bash
# The suite: every test/test_*.py, in Chrome with WebMCP on (test/page.py).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uvx --quiet --with playwright python -m unittest discover -s test -p 'test_*.py'
