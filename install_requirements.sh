#!/bin/bash

# SWE-bench Pipeline Installation Script
# This script installs all required dependencies for the pipeline

set -e  # Exit on any error

echo "🚀 Installing SWE-bench Pipeline Dependencies"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip and try again."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core requirements
echo "📥 Installing core requirements..."
pip install -r requirements-core.txt

# Ask user if they want to install full requirements
echo ""
echo "🤔 Do you want to install additional optional dependencies? (y/n)"
echo "   This includes development tools, monitoring, and cloud integration."
read -p "   Enter your choice: " choice

if [[ $choice == "y" || $choice == "Y" ]]; then
    echo "📥 Installing full requirements..."
    pip install -r requirements.txt
    echo "✅ Full requirements installed!"
else
    echo "✅ Core requirements installed!"
fi

# Check if Docker is available (for real SWE-bench evaluation)
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version)"
    echo "   Real SWE-bench evaluation will be available!"
else
    echo "⚠️  Docker not found. Real SWE-bench evaluation requires Docker."
    echo "   Install Docker Desktop to enable full evaluation capabilities."
fi

echo ""
echo "🎉 Installation completed!"
echo ""
echo "To activate the virtual environment in the future:"
echo "   source venv/bin/activate"
echo ""
echo "To run the pipeline:"
echo "   python pipeline/run_full_pipeline.py --limit 5"
echo ""
echo "For more information, see:"
echo "   - pipeline/EVALUATION_STATUS.md"
echo "   - pipeline/swebench_gen/README_injection_testing.md"
echo "   - pipeline/swebench_eval/README.md"
