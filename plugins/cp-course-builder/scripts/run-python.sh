#!/usr/bin/env sh
# run-python.sh: run a plugin script with a working Python 3 on macOS, Linux or Windows (Git Bash).
#   sh run-python.sh <script.py> [args...]
# Windows ships a "python3" placeholder that only opens the Microsoft Store, and macOS and
# Linux often lack "python", so each candidate is tried before use. The first that really
# runs Python 3.8 or later wins.
for cand in python3 python "py -3"; do
  if $cand -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    exec $cand "$@"
  fi
done
echo "No working Python 3.8 or later found. Install Python 3 so that python3, python or py is on PATH." >&2
exit 1
