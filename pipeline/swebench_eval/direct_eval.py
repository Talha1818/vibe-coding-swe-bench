#!/usr/bin/env python3
"""
Direct SWE-bench Evaluation Script
Uses the SWE-bench Python API directly to evaluate generated patches.
"""

from __future__ import annotations
import argparse
import json
import os
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

def run_swebench_evaluation(
    patch_records: List[Dict[str, Any]],
    model_name: str,
    injection_type: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Run SWE-bench evaluation using the Python API."""
    
    try:
        import swebench
        from swebench import run_evaluation, get_eval_report
    except ImportError:
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "success": False,
            "error": "SWE-bench not installed"
        }
    
    # Create model-specific output directory
    model_output_dir = output_dir / f"{model_name}_{injection_type}"
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running evaluation for {model_name} ({injection_type})")
    print(f"Number of patches: {len(patch_records)}")
    print(f"Output directory: {model_output_dir}")
    
    # Convert patch records to SWE-bench format
    predictions = []
    for record in patch_records:
        predictions.append({
            "instance_id": record["instance_id"],
            "model_name_or_path": record["model_name_or_path"],
            "model_patch": record["model_patch"]
        })
    
    try:
        # Run the evaluation
        print("Starting SWE-bench evaluation...")
        results = run_evaluation(
            predictions=predictions,
            log_dir=str(model_output_dir),
            timeout=300,
            verbose=True
        )
        
        # Get evaluation report
        report = get_eval_report(results)
        
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "output_dir": str(model_output_dir),
            "success": True,
            "num_patches": len(patch_records),
            "results": results,
            "report": report
        }
        
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "output_dir": str(model_output_dir),
            "success": False,
            "num_patches": len(patch_records),
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Direct SWE-bench evaluation")
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
    
    print(f"🚀 Starting direct SWE-bench evaluation")
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
            
            # Run evaluation
            eval_result = run_swebench_evaluation(
                patch_records=patches,
                model_name=model_name,
                injection_type=injection_type,
                output_dir=output_dir
            )
            
            all_results.append(eval_result)
    
    # Save summary
    summary_file = output_dir / "evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
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
                if 'report' in result:
                    print(f"      Report: {result['report']}")
            else:
                print(f"  ❌ {result['model_name']} ({result['injection_type']}): FAILED")
                if 'error' in result:
                    print(f"      Error: {result['error']}")

if __name__ == "__main__":
    main()
