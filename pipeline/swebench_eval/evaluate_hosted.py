#!/usr/bin/env python3
"""
Hosted SWE-bench evaluation script using sb-cli.
"""
import json
import sys
import subprocess
from pathlib import Path

def main():
    """Run hosted evaluation on generated patches."""
    
    if len(sys.argv) < 2:
        print("Usage: python evaluate_hosted.py <predictions_file> [subset]")
        print("Example: python evaluate_hosted.py ../swebench_gen/results/openai_gpt-4o/none_20250916_213114.jsonl swe-bench_lite")
        print("\nAvailable subsets:")
        print("  - swe-bench_lite (recommended for testing)")
        print("  - swe-bench_verified")
        print("  - swe-bench")
        sys.exit(1)
    
    pred_path = sys.argv[1]
    subset = sys.argv[2] if len(sys.argv) > 2 else "swe-bench_lite"
    
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
    
    # Run hosted evaluation using sb-cli
    print(f"\n🚀 Submitting to hosted SWE-bench evaluation...")
    print(f"This will upload your predictions to the hosted evaluator.")
    
    cmd = [
        "sb-cli", "submit", subset, "test",
        "--predictions_path", pred_path
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n✅ Evaluation submitted successfully!")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print("\n📊 Check the hosted evaluation results at:")
        print("   https://swebench.com")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Evaluation submission failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Evaluation submission failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
