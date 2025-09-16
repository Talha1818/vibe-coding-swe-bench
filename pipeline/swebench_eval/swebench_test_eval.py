#!/usr/bin/env python3
"""
SWE-bench Test Evaluation Script
Uses the official SWE-bench evaluation harness to run actual test cases.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import tempfile
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

def run_swebench_test_evaluation(
    predictions_file: Path,
    model_name: str,
    injection_type: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Run SWE-bench test evaluation using the official harness."""
    
    # Create model-specific output directory
    model_output_dir = output_dir / f"{model_name}_{injection_type}"
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running SWE-bench test evaluation for {model_name} ({injection_type})")
    print(f"Predictions file: {predictions_file}")
    print(f"Output directory: {model_output_dir}")
    
    # Method 1: Try using swebench-harness directly
    try:
        print("\n🔬 Attempting SWE-bench harness evaluation...")
        
        # Create a temporary script to run the evaluation
        eval_script = model_output_dir / "run_eval.py"
        with open(eval_script, 'w') as f:
            f.write(f"""
import sys
import os
sys.path.append('/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval')

try:
    from swebench import run_evaluation, get_eval_report
    import json
    
    # Load predictions
    predictions = []
    with open('{predictions_file}', 'r') as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line.strip()))
    
    print(f"Loaded {{len(predictions)}} predictions")
    
    # Run evaluation
    results = run_evaluation(
        predictions=predictions,
        log_dir='{model_output_dir}',
        timeout=300,
        verbose=True
    )
    
    # Get report
    report = get_eval_report(results)
    
    # Save results
    with open('{model_output_dir}/evaluation_results.json', 'w') as f:
        json.dump({{
            'results': results,
            'report': report
        }}, f, indent=2)
    
    print("Evaluation completed successfully")
    print(f"Results: {{report}}")
    
except Exception as e:
    print(f"Evaluation failed: {{e}}")
    import traceback
    traceback.print_exc()
""")
        
        # Run the evaluation script
        result = subprocess.run(
            ["python", str(eval_script)],
            cwd=model_output_dir,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        print(f"Evaluation script output:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            # Try to load results
            results_file = model_output_dir / "evaluation_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    eval_data = json.load(f)
                
                return {
                    "model_name": model_name,
                    "injection_type": injection_type,
                    "predictions_file": str(predictions_file),
                    "output_dir": str(model_output_dir),
                    "success": True,
                    "method": "swebench_harness",
                    "results": eval_data.get('report', {}),
                    "raw_results": eval_data.get('results', {})
                }
    
    except Exception as e:
        print(f"SWE-bench harness evaluation failed: {e}")
    
    # Method 2: Try using the command line interface
    try:
        print("\n🔬 Attempting command line evaluation...")
        
        cmd = [
            "python", "-c", f"""
import sys
sys.path.append('/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval')

# Try to run evaluation using the harness module
try:
    from swebench.harness.run_evaluation import main as run_eval_main
    import sys
    
    # Set up arguments for the evaluation
    sys.argv = [
        'run_evaluation',
        '--dataset_name', 'princeton-nlp/SWE-bench',
        '--split', 'test',
        '--predictions_path', '{predictions_file}',
        '--log_dir', '{model_output_dir}',
        '--timeout', '300',
        '--max_workers', '1'
    ]
    
    run_eval_main()
    print("Command line evaluation completed")
    
except Exception as e:
    print(f"Command line evaluation failed: {{e}}")
    import traceback
    traceback.print_exc()
"""
        ]
        
        result = subprocess.run(cmd, cwd=model_output_dir, capture_output=True, text=True, timeout=600)
        
        print(f"Command line output:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            return {
                "model_name": model_name,
                "injection_type": injection_type,
                "predictions_file": str(predictions_file),
                "output_dir": str(model_output_dir),
                "success": True,
                "method": "command_line",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    
    except Exception as e:
        print(f"Command line evaluation failed: {e}")
    
    # If all methods fail, return failure
    return {
        "model_name": model_name,
        "injection_type": injection_type,
        "predictions_file": str(predictions_file),
        "output_dir": str(model_output_dir),
        "success": False,
        "error": "All evaluation methods failed"
    }

def main():
    parser = argparse.ArgumentParser(description="SWE-bench test evaluation with actual test execution")
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
    
    print(f"🧪 Starting SWE-bench Test Evaluation")
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
            eval_result = run_swebench_test_evaluation(
                predictions_file=predictions_file,
                model_name=model_name,
                injection_type=injection_type,
                output_dir=output_dir
            )
            
            eval_result["num_patches"] = num_patches
            all_results.append(eval_result)
    
    # Save summary
    summary_file = output_dir / "test_evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Test evaluation completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Summary: {summary_file}")
    
    # Print results
    print(f"\n📊 TEST EVALUATION RESULTS:")
    print("="*60)
    
    successful_evals = 0
    for result in all_results:
        model = result['model_name']
        injection = result['injection_type']
        success = result.get('success', False)
        
        print(f"\n🤖 {model} ({injection}):")
        if success:
            successful_evals += 1
            method = result.get('method', 'unknown')
            print(f"  • ✅ Evaluation successful ({method})")
            
            if 'results' in result:
                results_data = result['results']
                print(f"  • Results: {results_data}")
        else:
            print(f"  • ❌ Evaluation failed")
            if 'error' in result:
                print(f"  • Error: {result['error']}")
    
    print(f"\n📈 Summary: {successful_evals}/{len(all_results)} evaluations successful")

if __name__ == "__main__":
    main()
