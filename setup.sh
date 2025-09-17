#!/bin/bash

# Setup script for vibe-coding SWE-bench generation pipeline
# This script activates a conda environment and installs required dependencies

set -e  # Exit on any error

echo "Setting up vibe-coding environment..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    echo "Please install Anaconda or Miniconda first"
    exit 1
fi

# Create conda environment if it doesn't exist (in /root)
if ! conda env list | grep -q "/root/vibe-code"; then
    echo "Creating conda environment 'vibe-code' in /root..."
    conda create -p /root/vibe-code python=3.11 -y
else
    echo "Conda environment '/root/vibe-code' already exists"
fi

# Activate the environment
echo "Activating conda environment '/root/vibe-code'..."
eval "$(conda shell.bash hook)"
conda activate /root/vibe-code

# Install inspect-ai and related dependencies
echo "Installing inspect-ai and dependencies..."
pip install inspect-ai

# Install additional dependencies used in the project
echo "Installing additional dependencies..."
pip install datasets

# Install any other commonly needed packages for ML/AI work
pip install openai requests

echo ""
echo "Setup complete! 🎉"
echo ""
echo "To activate the environment manually, run:"
echo "conda activate /root/vibe-code"
echo ""
echo "To run the SWE-bench generation pipeline:"
echo "python run.py --model <model_name> --split <split_name>"
echo ""
echo "Example:"
echo "python run.py --model openai/gpt-4 --split SWE-bench_Lite --limit 10"
