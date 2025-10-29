#!/bin/bash

# Financial Spending Analyzer - Startup Script

echo "==================================="
echo "Financial Spending Analyzer"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher to run this application."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    echo "Please install pip to manage Python packages."
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

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo ""
echo "==================================="
echo "Starting application..."
echo "==================================="
echo ""
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask application
python app.py
