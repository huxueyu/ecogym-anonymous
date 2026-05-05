#!/bin/bash


echo "=========================================="
echo "Operation Bench — Human study interface"
echo "=========================================="
echo ""

echo "Checking dependencies..."
python3 -c "import flask, flask_cors, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install flask flask-cors pyyaml
else
    echo "✅ All dependencies installed"
fi

echo ""
echo "Starting study server..."
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR"
python3 operation_server.py

