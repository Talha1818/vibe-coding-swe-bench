#!/usr/bin/env python3
"""
Local SWE-bench evaluation script using the official harness.
"""
import json
import sys
import subprocess
from pathlib import Path

def main():
    """Run local evaluation on generated patches."""
    
    if len(sys.argv) < 2:
        print("Usage: python evaluate_local.py <predictions_file> [subset]")
        print("Example: python evaluate_local.py ../swebench_gen/results/openai_gpt-4o/none_20250916_213114.jsonl SWE-bench_Lite")
        sys.exit(1)
    
    pred_path = sys.argv[1]
    subset = sys.argv[2] if len(sys.argv) > 2 else "SWE-bench_Lite"
    
    print(f"🔍 Loading predictions from: {pred_path}")
    print(f"📊 Using dataset subset: {subset}")
    
    # Validate prediction format first
    try:
        with open(pred_path) as f:
            preds = [json.loads(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ File not found: {pred_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in predictions file: {e}")
        sys.exit(1)
    
    print(f"📝 Loaded {len(preds)} predictions")
    
    # Validate prediction format
    required_keys = ["instance_id", "model_name_or_path", "model_patch"]
    for i, pred in enumerate(preds):
        missing_keys = [key for key in required_keys if key not in pred]
        if missing_keys:
            print(f"❌ Prediction {i} missing required keys: {missing_keys}")
            sys.exit(1)
    
    print("✅ Prediction format validation passed")
    
    # Run evaluation using command line interface
    print("\n🚀 Starting SWE-bench evaluation...")
    print("This will spin up Docker containers and run tests. This may take a while...")
    
    cmd = [
        "python", "-m", "swebench.harness.run_evaluation",
        "--dataset_name", f"princeton-nlp/{subset}",
        "--predictions_path", pred_path,
        "--max_workers", "4",  # Conservative for testing
        "--run_id", f"eval_{Path(pred_path).stem}"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n✅ Evaluation completed!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Evaluation failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
