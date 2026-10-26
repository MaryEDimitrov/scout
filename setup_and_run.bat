@echo off
REM One command: create a virtual environment, install pinned packages, start the app.
REM Usage (Windows):  setup_and_run.bat
cd /d "%~dp0"
if not exist .venv (
  echo Creating virtual environment (.venv)...
  python -m venv .venv || (echo Please install Python 3.11 or newer from https://www.python.org/downloads/ & exit /b 1)
)
echo Installing packages (first time takes about a minute)...
.venv\Scripts\python -m pip install --quiet --upgrade pip
.venv\Scripts\python -m pip install --quiet -r requirements.txt
echo Starting Scout at http://localhost:8501 (press Ctrl+C to stop)...
.venv\Scripts\python -m streamlit run app.py --server.port 8501
