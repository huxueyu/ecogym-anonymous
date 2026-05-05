@echo off


echo ==========================================
echo Operation Bench — Human study interface
echo ==========================================
echo.

echo Checking dependencies...
python -c "import flask, flask_cors, yaml" 2>nul
if errorlevel 1 (
    echo Missing dependencies. Installing...
    pip install flask flask-cors pyyaml
) else (
    echo All dependencies installed
)

echo.
echo Starting backend server...
echo.


cd /d "%~dp0"


python operation_server.py

