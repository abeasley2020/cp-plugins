#!/usr/bin/env bash
# build.sh: same as build.py, for Git Bash, macOS and Linux.
#   bash build.sh <work-folder> [module|week] [unit list, e.g. 1,2]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ARGS=("$1")
[ -n "${2:-}" ] && ARGS+=(--format "$2")
[ -n "${3:-}" ] && ARGS+=(--units "$3")
exec sh "$HERE/run-python.sh" "$HERE/build.py" "${ARGS[@]}"
