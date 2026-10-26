@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   Customer Segmentation ^& Clustering - Project Startup
echo ============================================================
echo.

:: ---------------------------------------------------------------
:: STEP 1 - Check Python
:: ---------------------------------------------------------------
echo [Step 1/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python is not installed or not found in PATH.
    echo  Please install Python 3.10+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v
echo.

:: ---------------------------------------------------------------
:: STEP 2 - Check Node.js
:: ---------------------------------------------------------------
echo [Step 2/8] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Node.js is not installed or not found in PATH.
    echo  Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo  Found: Node.js %%v
echo.

:: ---------------------------------------------------------------
:: STEP 3 - Check npm
:: ---------------------------------------------------------------
echo [Step 3/8] Checking npm installation...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm is not installed or not found in PATH.
    echo  npm is bundled with Node.js. Please reinstall Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo  Found: npm v%%v
echo.

:: ---------------------------------------------------------------
:: STEP 4 - Create Python virtual environment (if needed)
:: ---------------------------------------------------------------
echo [Step 4/8] Setting up Python virtual environment...
if not exist "backend\venv" (
    echo  Creating virtual environment at backend\venv ...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo.
        echo  ERROR: Failed to create virtual environment.
        echo  Ensure the 'venv' module is available (it ships with Python 3.3+).
        echo.
        pause
        exit /b 1
    )
    echo  Virtual environment created successfully.
) else (
    echo  Virtual environment already exists, skipping creation.
)
echo.

:: ---------------------------------------------------------------
:: STEP 5 - Activate venv and install Python requirements
:: ---------------------------------------------------------------
echo [Step 5/8] Installing Python dependencies...
call backend\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Could not activate virtual environment.
    echo.
    pause
    exit /b 1
)

pip install -r backend\requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: pip install failed. Check backend\requirements.txt and your internet connection.
    echo.
    call deactivate
    pause
    exit /b 1
)
echo  Python dependencies installed successfully.

call deactivate
echo.

:: ---------------------------------------------------------------
:: STEP 6 - Install Node / npm dependencies
:: ---------------------------------------------------------------
echo [Step 6/8] Installing Node.js dependencies...
cd frontend
npm install --silent
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: npm install failed. Check frontend\package.json and your internet connection.
    echo.
    cd ..
    pause
    exit /b 1
)
echo  Node.js dependencies installed successfully.
cd ..
echo.

:: ---------------------------------------------------------------
:: STEP 7 - Launch Backend in a new terminal window
:: ---------------------------------------------------------------
echo [Step 7/8] Launching Backend server...
START "Customer Segmentation - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python run.py"
echo  Backend window opened.
echo.

:: Short pause to let backend start before frontend
timeout /t 3 /nobreak >nul

:: ---------------------------------------------------------------
:: STEP 8 - Launch Frontend in a new terminal window
:: ---------------------------------------------------------------
echo [Step 8/8] Launching Frontend dev server...
START "Customer Segmentation - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo  Frontend window opened.
echo.

:: ---------------------------------------------------------------
:: Display URLs
:: ---------------------------------------------------------------
echo ============================================================
echo   All services are starting up!
echo ============================================================
echo.
echo   Backend API   :  http://localhost:8000
echo   Frontend App  :  http://localhost:5173
echo   API Docs      :  http://localhost:8000/docs
echo   ReDoc         :  http://localhost:8000/redoc
echo.
echo   Note: It may take a few seconds for both servers to be ready.
echo   You can close this window - the servers run in their own windows.
echo.
echo ============================================================
pause
endlocal
