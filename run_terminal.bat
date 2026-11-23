@echo off
REM =============================================================
REM  run_terminal.bat — Windows launcher for terminal_app.py
REM  School Lab Inventory Manager | CBSE Class 12 CS Project
REM
REM  HOW TO USE:
REM    Double-click this file  OR  run from Command Prompt:
REM      run_terminal.bat
REM
REM  This script automatically creates the virtual environment
REM  if it is missing, installs mysql-connector-python, and
REM  launches terminal_app.py using the venv Python.
REM =============================================================

echo.

REM --- Step 1: Create venv if missing --------------------------
IF NOT EXIST "venv\" (
    echo   [Setup] venv not found. Creating virtual environment...
    python -m venv venv
    echo   [Setup] Virtual environment created.
)

REM --- Step 2: Install mysql-connector-python if missing -------
venv\Scripts\python.exe -c "import mysql.connector" >nul 2>&1
IF ERRORLEVEL 1 (
    echo   [Setup] Installing mysql-connector-python...
    venv\Scripts\pip.exe install --quiet mysql-connector-python
    echo   [Setup] Installation complete.
)

REM --- Step 3: Launch terminal app -----------------------------
echo.
venv\Scripts\python.exe terminal_app.py
pause
