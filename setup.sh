#!/bin/bash
# Setup script for Sprint Connect - macOS/Linux

echo "==================================="
echo "Sprint Connect Setup Script"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo ""
echo "Initializing database..."
python init_db.py

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the backend (Terminal 1):"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "3. Start the frontend (Terminal 2):"
echo "   streamlit run app.py"
echo ""
echo "Demo accounts:"
echo "  Student: sarah@srh.nl / demo123"
echo "  Admin: admin@srh.nl / admin123"
echo ""
