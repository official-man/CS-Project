@echo off
REM =============================================================
REM  run_gui.bat — Windows launcher for gui_app.py
REM  School Lab Inventory Manager | CBSE Class 12 CS Project
REM
REM  HOW TO USE:
REM    Double-click this file  OR  run from Command Prompt:
REM      run_gui.bat
REM =============================================================

echo.

IF NOT EXIST "venv\" (
    echo   [Setup] venv not found. Creating virtual environment...
    python -m venv venv
    echo   [Setup] Virtual environment created.
)

venv\Scripts\python.exe -c "import mysql.connector" >nul 2>&1
IF ERRORLEVEL 1 (
    echo   [Setup] Installing mysql-connector-python...
    venv\Scripts\pip.exe install --quiet mysql-connector-python
    echo   [Setup] Installation complete.
)

echo.
venv\Scripts\python.exe gui_app.py
