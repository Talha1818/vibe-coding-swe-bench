#!/bin/bash

echo "🔧 Setting up SWE-bench evaluation environment..."

# Create conda environment if it doesn't exist
if ! conda env list | grep -q "swebench-eval"; then
    echo "Creating conda environment: swebench-eval"
    conda create -n swebench-eval python=3.9 -y
fi

# Activate environment
echo "Activating conda environment..."
conda activate swebench-eval

# Install SWE-bench evaluation harness
echo "Installing SWE-bench evaluation harness..."
pip install swebench

# Install additional dependencies
echo "Installing additional dependencies..."
pip install datasets transformers torch

# Install git (needed for patch application)
echo "Installing git..."
conda install git -y

echo "✅ Setup completed!"
echo ""
echo "To use the evaluation pipeline:"
echo "1. Activate the environment: conda activate swebench-eval"
echo "2. Run evaluation: python evaluate_patches.py --install_deps"
echo ""
