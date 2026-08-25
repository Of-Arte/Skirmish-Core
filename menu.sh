#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MENU_SCRIPT="${SCRIPT_DIR}/skirmish/menu.py"

if ! command -v python3 &> /dev/null; then
  echo "====================================================="
  echo "  [ERROR] PYTHON 3 IS REQUIRED TO RUN THIS MENU"
  echo "====================================================="
  echo
  echo "Python 3 is not installed or not found in system PATH."
  echo "Please install python3 (e.g. sudo apt install python3)."
  echo "====================================================="
  exit 1
fi

if [ ! -f "${MENU_SCRIPT}" ]; then
  echo "====================================================="
  echo "  [ERROR] MENU SCRIPT NOT FOUND"
  echo "====================================================="
  echo "Could not locate menu.py at ${MENU_SCRIPT}"
  exit 1
fi

exec python3 "${MENU_SCRIPT}" "$@"
