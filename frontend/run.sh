#!/bin/bash
# Startup script for DDoS Detection Dashboard

echo "================================"
echo "DDoS Detection Dashboard"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask app
echo ""
echo "================================"
echo "Starting Flask server..."
echo "Dashboard: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "================================"
echo ""
python app.py
