#!/usr/bin/env python3
"""
Simple SWE-bench Evaluation Script
Uses the official SWE-bench evaluation harness to evaluate generated patches.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def load_patch_results(results_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load all patch results from the swebench_gen results directory."""
    patch_data = {}
    
    # Find all model directories
    for model_dir in results_dir.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            patch_data[model_name] = []
            
            # Load all JSON files in the model directory
            for json_file in model_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                patch_record = json.loads(line.strip())
                                patch_record['source_file'] = str(json_file)
                                patch_data[model_name].append(patch_record)
                except Exception as e:
                    print(f"Warning: Could not load {json_file}: {e}")
    
    return patch_data

def create_predictions_file(patch_records: List[Dict[str, Any]], output_file: Path) -> int:
    """Create a predictions.jsonl file from patch records."""
    with open(output_file, 'w') as f:
        for record in patch_records:
            # Create SWE-bench compatible record
            prediction_record = {
                "instance_id": record["instance_id"],
                "model_name_or_path": record["model_name_or_path"],
                "model_patch": record["model_patch"]
            }
            f.write(json.dumps(prediction_record) + "\n")
    
    return len(patch_records)

def run_swebench_eval_command(
    predictions_file: Path,
    output_dir: Path,
    model_name: str,
    injection_type: str
) -> Dict[str, Any]:
    """Run SWE-bench evaluation using the official command."""
    
    # Create model-specific output directory
    model_output_dir = output_dir / f"{model_name}_{injection_type}"
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the evaluation command
    # This uses the official SWE-bench evaluation command
    cmd = [
        "python", "-m", "swebench",
        "--predictions_path", str(predictions_file),
        "--swe_bench_tasks", "princeton-nlp/SWE-bench",
        "--log_dir", str(model_output_dir),
        "--timeout", "300",
        "--verbose"
    ]
    
    print(f"Running evaluation for {model_name} ({injection_type})")
    print(f"Command: {' '.join(cmd)}")
    print(f"Output directory: {model_output_dir}")
    
    try:
        # Run the evaluation
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Save the raw output
        with open(model_output_dir / "evaluation_output.txt", 'w') as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
        
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(model_output_dir),
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(model_output_dir),
            "success": False,
            "return_code": -1,
            "error": "Evaluation timed out"
        }
    except Exception as e:
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(model_output_dir),
            "success": False,
            "return_code": -1,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Simple SWE-bench evaluation")
    parser.add_argument("--results_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_gen/results",
                       help="Directory containing patch results")
    parser.add_argument("--output_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results",
                       help="Directory to save evaluation results")
    parser.add_argument("--model", 
                       help="Specific model to evaluate (default: all)")
    parser.add_argument("--injection_type", 
                       help="Specific injection type to evaluate (default: all)")

    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Starting SWE-bench evaluation")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    
    # Load patch data
    patch_data = load_patch_results(results_dir)
    
    if not patch_data:
        print("No patch data found!")
        return
    
    print(f"Found patch data for models: {list(patch_data.keys())}")
    
    all_results = []
    
    for model_name, patch_records in patch_data.items():
        if args.model and model_name != args.model:
            continue
            
        print(f"\n📊 Processing model: {model_name}")
        print(f"Found {len(patch_records)} patch records")
        
        # Group patches by injection type
        patches_by_injection = {}
        for record in patch_records:
            injection_type = record.get("injection_type", "none")
            if args.injection_type and injection_type != args.injection_type:
                continue
                
            if injection_type not in patches_by_injection:
                patches_by_injection[injection_type] = []
            patches_by_injection[injection_type].append(record)
        
        # Evaluate each injection type
        for injection_type, patches in patches_by_injection.items():
            if not patches:
                continue
                
            print(f"\n🔍 Evaluating {injection_type} injection ({len(patches)} patches)")
            
            # Create predictions file
            predictions_file = output_dir / f"{model_name}_{injection_type}_predictions.jsonl"
            num_patches = create_predictions_file(patches, predictions_file)
            print(f"Created predictions file with {num_patches} patches")
            
            # Run evaluation
            eval_result = run_swebench_eval_command(
                predictions_file=predictions_file,
                output_dir=output_dir,
                model_name=model_name,
                injection_type=injection_type
            )
            
            eval_result["num_patches"] = num_patches
            all_results.append(eval_result)
    
    # Save summary
    summary_file = output_dir / "evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Evaluation completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Summary: {summary_file}")
    
    successful_evals = sum(1 for r in all_results if r.get('success', False))
    total_evals = len(all_results)
    print(f"Successful evaluations: {successful_evals}/{total_evals}")
    
    if successful_evals > 0:
        print("\n📊 Evaluation Results:")
        for result in all_results:
            if result.get('success', False):
                print(f"  ✅ {result['model_name']} ({result['injection_type']}): {result.get('num_patches', 0)} patches")
            else:
                print(f"  ❌ {result['model_name']} ({result['injection_type']}): FAILED")
                if 'error' in result:
                    print(f"      Error: {result['error']}")

if __name__ == "__main__":
    main()
