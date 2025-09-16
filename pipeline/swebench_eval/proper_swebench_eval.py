#!/usr/bin/env python3
"""
Proper SWE-bench Evaluation Script
Uses the correct SWE-bench evaluation harness API with all required parameters.
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

def create_predictions_file(patch_records: List[Dict[str, Any]], output_file: Path) -> List[str]:
    """Create a predictions.jsonl file from patch records and return instance IDs."""
    instance_ids = []
    
    with open(output_file, 'w') as f:
        for record in patch_records:
            # Create SWE-bench compatible record
            prediction_record = {
                "instance_id": record["instance_id"],
                "model_name_or_path": record["model_name_or_path"],
                "model_patch": record["model_patch"]
            }
            f.write(json.dumps(prediction_record) + "\n")
            instance_ids.append(record["instance_id"])
    
    return instance_ids

def run_swebench_evaluation(
    predictions_file: Path,
    instance_ids: List[str],
    model_name: str,
    injection_type: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Run SWE-bench evaluation using the proper API."""
    
    # Create model-specific output directory
    model_output_dir = output_dir / f"{model_name}_{injection_type}"
    model_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running SWE-bench evaluation for {model_name} ({injection_type})")
    print(f"Instance IDs: {instance_ids}")
    print(f"Predictions file: {predictions_file}")
    print(f"Output directory: {model_output_dir}")
    
    try:
        from swebench import run_evaluation
        
        print("\n🔬 Starting SWE-bench evaluation...")
        
        # Call the evaluation function with all required parameters
        results = run_evaluation(
            dataset_name="princeton-nlp/SWE-bench",
            split="test",
            instance_ids=instance_ids,
            predictions_path=str(predictions_file),
            max_workers=1,  # Use single worker for simplicity
            force_rebuild=False,
            cache_level="none",  # Don't use cache for testing
            clean=False,
            open_file_limit=1024,
            run_id=f"{model_name}_{injection_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timeout=300,  # 5 minutes timeout
            namespace=None,
            rewrite_reports=True,
            modal=False,  # Don't use Modal cloud
            instance_image_tag="latest",
            env_image_tag="latest",
            report_dir=str(model_output_dir)
        )
        
        print("✅ SWE-bench evaluation completed successfully!")
        
        # Try to get evaluation report
        try:
            from swebench import get_eval_report
            report = get_eval_report(results)
            print(f"Evaluation report: {report}")
        except Exception as e:
            print(f"Warning: Could not get evaluation report: {e}")
            report = None
        
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(model_output_dir),
            "success": True,
            "results": results,
            "report": report,
            "instance_ids": instance_ids
        }
        
    except Exception as e:
        print(f"❌ SWE-bench evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "model_name": model_name,
            "injection_type": injection_type,
            "predictions_file": str(predictions_file),
            "output_dir": str(model_output_dir),
            "success": False,
            "error": str(e),
            "instance_ids": instance_ids
        }

def main():
    parser = argparse.ArgumentParser(description="Proper SWE-bench evaluation with correct API")
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
    
    print(f"🧪 Starting Proper SWE-bench Evaluation")
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
            instance_ids = create_predictions_file(patches, predictions_file)
            print(f"Created predictions file with {len(instance_ids)} patches")
            print(f"Instance IDs: {instance_ids}")
            
            # Run evaluation
            eval_result = run_swebench_evaluation(
                predictions_file=predictions_file,
                instance_ids=instance_ids,
                model_name=model_name,
                injection_type=injection_type,
                output_dir=output_dir
            )
            
            eval_result["num_patches"] = len(patches)
            all_results.append(eval_result)
    
    # Save summary
    summary_file = output_dir / "proper_evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Proper evaluation completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Summary: {summary_file}")
    
    # Print results
    print(f"\n📊 EVALUATION RESULTS:")
    print("="*60)
    
    successful_evals = 0
    for result in all_results:
        model = result['model_name']
        injection = result['injection_type']
        success = result.get('success', False)
        
        print(f"\n🤖 {model} ({injection}):")
        if success:
            successful_evals += 1
            print(f"  • ✅ Evaluation successful")
            
            if 'report' in result and result['report']:
                print(f"  • Report: {result['report']}")
            
            if 'results' in result:
                print(f"  • Results available in: {result['output_dir']}")
        else:
            print(f"  • ❌ Evaluation failed")
            if 'error' in result:
                print(f"  • Error: {result['error']}")
    
    print(f"\n📈 Summary: {successful_evals}/{len(all_results)} evaluations successful")

if __name__ == "__main__":
    main()
