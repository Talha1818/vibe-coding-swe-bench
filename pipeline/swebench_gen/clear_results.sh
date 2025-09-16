#!/bin/bash

echo "🧹 Clearing results and logs..."
rm -rf logs/
rm -rf results/

echo "✅ Cleared logs/ and results/ directories"

echo "🚀 Starting multi-model evaluation..."
python multi_model_runner.py --limit 5

echo "✅ Multi-model evaluation completed!"
