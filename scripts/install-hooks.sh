#!/bin/sh
# Points this checkout's git at the committed hooks in .githooks/. Run once after cloning.
set -eu
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "Hooks installed: pre-commit, commit-msg, and pre-push (owner-locked to cocodedk) are active."
