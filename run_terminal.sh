#!/usr/bin/env bash
# =============================================================
#  run_terminal.sh — Linux / Archcraft launcher for terminal_app.py
#  School Lab Inventory Manager | CBSE Class 12 CS Project
#
#  HOW TO USE:
#    1. Open a terminal in this project folder.
#    2. First time only: chmod +x run_terminal.sh
#    3. Run: ./run_terminal.sh
#
#  This script automatically creates the virtual environment if
#  it is missing, installs the MySQL connector driver inside it,
#  and then launches terminal_app.py using the venv Python.
# =============================================================

set -e   # stop immediately on any error

# --- Step 1: Check if the venv folder exists -----------------
if [ ! -d "venv" ]; then
    echo ""
    echo "  [Setup] 'venv' folder not found. Creating virtual environment..."
    python3 -m venv venv
    echo "  [Setup] Virtual environment created."
fi

# --- Step 2: Check if mysql.connector is installed -----------
if ! venv/bin/python -c "import mysql.connector" 2>/dev/null; then
    echo "  [Setup] Installing mysql-connector-python inside venv..."
    venv/bin/pip install --quiet mysql-connector-python
    echo "  [Setup] Installation complete."
fi

# --- Step 3: Launch the terminal app -------------------------
echo ""
venv/bin/python terminal_app.py
