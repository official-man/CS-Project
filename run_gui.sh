#!/usr/bin/env bash
# =============================================================
#  run_gui.sh — Linux / Archcraft launcher for gui_app.py
#  School Lab Inventory Manager | CBSE Class 12 CS Project
#
#  HOW TO USE:
#    1. Open a terminal in this project folder.
#    2. First time only: chmod +x run_gui.sh
#    3. Run: ./run_gui.sh
# =============================================================

set -e

if [ ! -d "venv" ]; then
    echo "  [Setup] 'venv' folder not found. Creating virtual environment..."
    python3 -m venv venv
    echo "  [Setup] Virtual environment created."
fi

if ! venv/bin/python -c "import mysql.connector" 2>/dev/null; then
    echo "  [Setup] Installing mysql-connector-python inside venv..."
    venv/bin/pip install --quiet mysql-connector-python
    echo "  [Setup] Installation complete."
fi

echo ""
venv/bin/python gui_app.py
