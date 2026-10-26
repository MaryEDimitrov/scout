#!/usr/bin/env bash
# One command: create a virtual environment, install pinned packages, check for the key, start the app.
# Usage (Mac/Linux):  bash setup_and_run.sh
set -e
cd "$(dirname "$0")"

PY=$(command -v python3 || command -v python)
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or newer is required"' \
  || { echo "Please install Python 3.11 or newer from https://www.python.org/downloads/"; exit 1; }

if [ ! -d .venv ]; then
  echo "Creating virtual environment (.venv)…"
  "$PY" -m venv .venv
fi
echo "Installing packages (first time takes about a minute)…"
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

if ! grep -qs "^PORTKEY_API_KEY=." .env ../.env; then
  echo "Note: no PORTKEY_API_KEY found in .env here or in the folder above."
  echo "      The app will start, and will explain where to put the key."
fi

echo "Starting Scout at http://localhost:8501 (press Ctrl+C to stop)…"
.venv/bin/python -m streamlit run app.py --server.port 8501
