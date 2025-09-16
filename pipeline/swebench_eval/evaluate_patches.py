#!/usr/bin/env python3
"""
SWE-bench Evaluation Pipeline
Evaluates generated patches from swebench_gen/results using SWE-bench evaluation harness.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile

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

def run_swebench_evaluation(
    predictions_file: Path,
    model_name: str,
    injection_type: str,
    output_dir: Path,
    timeout: int = 300
) -> Dict[str, Any]:
    """Run SWE-bench evaluation on a predictions file."""
    
    # Create output directory for this evaluation
    eval_output_dir = output_dir / f"{model_name}_{injection_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up environment
    env = os.environ.copy()
    env["SWEBENCH_EVAL_OUTPUT_DIR"] = str(eval_output_dir)
    
    # Build evaluation command
    # Note: This assumes SWE-bench evaluation harness is installed
    cmd = [
        "python", "-m", "swebench",
        "--predictions_path", str(predictions_file),
        "--swe_bench_tasks", "princeton-nlp/SWE-bench",
        "--log_dir", str(eval_output_dir),
        "--timeout", str(timeout),
        "--verbose"
    ]
    
    print(f"Running evaluation for {model_name} with {injection_type}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Output directory: {eval_output_dir}")
    
    try:
        # Run the evaluation
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        
        # Parse results
        results = {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(eval_output_dir),
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
        # Try to extract metrics from output
        try:
            # Look for results in the output directory
            results_files = list(eval_output_dir.glob("*.json"))
            if results_files:
                with open(results_files[0], 'r') as f:
                    eval_results = json.load(f)
                    results["evaluation_metrics"] = eval_results
        except Exception as e:
            print(f"Warning: Could not parse evaluation results: {e}")
        
        print(f"✅ Evaluation completed successfully")
        return results
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Evaluation failed: {e}")
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(eval_output_dir),
            "success": False,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "return_code": e.returncode,
            "error": str(e)
        }

def run_evaluation_pipeline(
    results_dir: Path,
    output_dir: Path,
    timeout: int = 300,
    models: Optional[List[str]] = None,
    injection_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Run evaluation pipeline on all or selected patch results."""
    
    print(f"Loading patch results from: {results_dir}")
    patch_data = load_patch_results(results_dir)
    
    if not patch_data:
        print("No patch data found!")
        return []
    
    print(f"Found patch data for models: {list(patch_data.keys())}")
    
    all_results = []
    
    for model_name, patch_records in patch_data.items():
        if models and model_name not in models:
            continue
            
        print(f"\n📊 Processing model: {model_name}")
        print(f"Found {len(patch_records)} patch records")
        
        # Group patches by injection type
        patches_by_injection = {}
        for record in patch_records:
            injection_type = record.get("injection_type", "none")
            if injection_types and injection_type not in injection_types:
                continue
                
            if injection_type not in patches_by_injection:
                patches_by_injection[injection_type] = []
            patches_by_injection[injection_type].append(record)
        
        # Evaluate each injection type
        for injection_type, patches in patches_by_injection.items():
            if not patches:
                continue
                
            print(f"\n🔍 Evaluating {injection_type} injection ({len(patches)} patches)")
            
            # Create temporary predictions file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_file:
                predictions_file = Path(tmp_file.name)
                num_patches = create_predictions_file(patches, predictions_file)
                print(f"Created predictions file with {num_patches} patches")
            
            try:
                # Run evaluation
                eval_result = run_swebench_evaluation(
                    predictions_file=predictions_file,
                    model_name=model_name,
                    injection_type=injection_type,
                    output_dir=output_dir,
                    timeout=timeout
                )
                
                eval_result["num_patches"] = num_patches
                all_results.append(eval_result)
                
            finally:
                # Clean up temporary file
                if predictions_file.exists():
                    predictions_file.unlink()
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Evaluate SWE-bench patches")
    parser.add_argument("--results_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_gen/results",
                       help="Directory containing patch results")
    parser.add_argument("--output_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results",
                       help="Directory to save evaluation results")
    parser.add_argument("--models", nargs="+", 
                       help="Specific models to evaluate (default: all)")
    parser.add_argument("--injection_types", nargs="+", 
                       help="Specific injection types to evaluate (default: all)")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout for each evaluation in seconds")
    parser.add_argument("--install_deps", action="store_true",
                       help="Install SWE-bench evaluation dependencies")

    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.install_deps:
        print("Installing SWE-bench evaluation dependencies...")
        try:
            subprocess.run(["pip", "install", "swebench"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return
    
    print(f"🚀 Starting SWE-bench evaluation pipeline")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    
    # Run evaluation pipeline
    eval_results = run_evaluation_pipeline(
        results_dir=results_dir,
        output_dir=output_dir,
        timeout=args.timeout,
        models=args.models,
        injection_types=args.injection_types
    )
    
    # Save summary
    summary_file = output_dir / "evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(eval_results, f, indent=2)
    
    print(f"\n✅ Evaluation pipeline completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Summary: {summary_file}")
    
    successful_evals = sum(1 for r in eval_results if r.get('success', False))
    total_evals = len(eval_results)
    print(f"Successful evaluations: {successful_evals}/{total_evals}")
    
    if successful_evals > 0:
        print("\n📊 Evaluation Results:")
        for result in eval_results:
            if result.get('success', False):
                print(f"  ✅ {result['model_name']} ({result['injection_type']}): {result.get('num_patches', 0)} patches")
            else:
                print(f"  ❌ {result['model_name']} ({result['injection_type']}): FAILED")

if __name__ == "__main__":
    main()
