@echo off
REM =============================================================
REM  run_gui.bat — Windows launcher for gui_app.py
REM  School Lab Inventory Manager | CBSE Class 12 CS Project
REM
REM  HOW TO USE:
REM    Double-click this file  OR  open Command Prompt here and run:
REM      run_gui.bat
REM =============================================================

@chcp 65001 >nul 2>&1

echo.
echo  ============================================
echo   School Lab Inventory Manager -- GUI Launch
echo  ============================================
echo.

REM --- Step 1: Detect Python command ---------------------------
python --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYCMD=python
    GOTO :found_python
)

py --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYCMD=py
    GOTO :found_python
)

echo  [ERROR] Python was not found on this computer.
echo.
echo  To fix this:
echo    1. Download Python from https://python.org/downloads
echo    2. During install, tick "Add Python to PATH"
echo    3. Re-run this file.
echo.
pause
EXIT /B 1

:found_python
echo  [OK] Python found: using '%PYCMD%'

REM --- Step 2: Create venv if missing --------------------------
IF NOT EXIST "venv\" (
    echo  [Setup] Creating virtual environment...
    %PYCMD% -m venv venv
    IF ERRORLEVEL 1 (
        echo  [ERROR] Failed to create virtual environment.
        echo  You may need administrator rights on this machine.
        pause
        EXIT /B 1
    )
    echo  [Setup] Virtual environment created.
)

REM --- Step 3: Install mysql-connector-python if missing --------
venv\Scripts\python.exe -c "import mysql.connector" >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [Setup] Installing mysql-connector-python...
    echo  [Setup] (Needs internet connection -- may take 30 seconds)
    venv\Scripts\pip.exe install --quiet mysql-connector-python
    IF ERRORLEVEL 1 (
        echo  [ERROR] pip install failed.
        echo  Check your internet connection and try again.
        pause
        EXIT /B 1
    )
    echo  [Setup] Installation complete.
)

REM --- Step 4: Launch the GUI app ------------------------------
echo.
echo  [OK] Launching gui_app.py ...
echo.
venv\Scripts\python.exe gui_app.py
