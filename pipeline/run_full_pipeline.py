#!/usr/bin/env python3
"""
Full SWE-bench Pipeline Runner
Clears results, runs generation, runs evaluation, and prints metrics.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def run_command(cmd: list, cwd: Path = None, description: str = "") -> bool:
    """Run a command and return success status."""
    if description:
        print(f"\n🔄 {description}")
    
    print(f"Command: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def clear_results(gen_dir: Path, eval_dir: Path) -> bool:
    """Clear all results directories."""
    print("\n🧹 Clearing results directories...")
    
    # Clear generation results
    if gen_dir.exists():
        import shutil
        shutil.rmtree(gen_dir)
        print(f"✅ Cleared {gen_dir}")
    
    # Clear evaluation results  
    if eval_dir.exists():
        import shutil
        shutil.rmtree(eval_dir)
        print(f"✅ Cleared {eval_dir}")
    
    return True

def run_generation(gen_dir: Path, limit: int = 5) -> bool:
    """Run the patch generation pipeline."""
    print(f"\n🚀 Running patch generation (limit: {limit})...")
    
    # Change to generation directory
    gen_script = gen_dir / "simple_parallel_runner.py"
    if not gen_script.exists():
        print(f"❌ Generation script not found: {gen_script}")
        return False
    
    cmd = ["python", "simple_parallel_runner.py", "--limit", str(limit)]
    return run_command(cmd, cwd=gen_dir, description="Patch generation")

def run_evaluation(eval_dir: Path) -> bool:
    """Run the patch evaluation pipeline."""
    print(f"\n🔍 Running patch evaluation...")
    
    # Change to evaluation directory
    eval_script = eval_dir / "patch_validator.py"
    if not eval_script.exists():
        print(f"❌ Evaluation script not found: {eval_script}")
        return False
    
    cmd = ["python", "patch_validator.py"]
    return run_command(cmd, cwd=eval_dir, description="Patch evaluation")

def run_real_evaluation(eval_dir: Path) -> bool:
    """Run real SWE-bench test evaluation."""
    print(f"\n🧪 Running real SWE-bench test evaluation...")
    
    # Change to evaluation directory
    eval_script = eval_dir / "swebench_test_eval.py"
    if not eval_script.exists():
        print(f"❌ Real evaluation script not found: {eval_script}")
        return False
    
    cmd = ["python", "swebench_test_eval.py"]
    return run_command(cmd, cwd=eval_dir, description="Real SWE-bench test evaluation")

def load_evaluation_results(eval_dir: Path) -> Dict[str, Any]:
    """Load evaluation results from the validation summary."""
    summary_file = eval_dir / "results" / "validation_summary.json"
    
    if not summary_file.exists():
        print(f"❌ Evaluation summary not found: {summary_file}")
        return {}
    
    try:
        with open(summary_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading evaluation results: {e}")
        return {}

def print_metrics(results: Dict[str, Any]) -> None:
    """Print comprehensive metrics from the evaluation results."""
    
    if not results:
        print("\n❌ No evaluation results to display")
        return
    
    print("\n" + "="*60)
    print("📊 SWE-BENCH PIPELINE RESULTS")
    print("="*60)
    
    # Overall metrics
    print(f"\n🎯 OVERALL METRICS:")
    print(f"  • Total patches generated: {results.get('total_patches', 0)}")
    print(f"  • Valid patches: {results.get('total_valid_patches', 0)}")
    print(f"  • Validity rate: {results.get('overall_validity_rate', 0):.1f}%")
    print(f"  • Models tested: {results.get('total_models', 0)}")
    print(f"  • Injection types: {results.get('total_injection_types', 0)}")
    
    # Per-model breakdown
    print(f"\n📈 PER-MODEL BREAKDOWN:")
    analyses = results.get('analyses', [])
    
    for analysis in analyses:
        model = analysis.get('model_name', 'Unknown')
        injection = analysis.get('injection_type', 'Unknown')
        patches = analysis.get('total_patches', 0)
        valid = analysis.get('valid_patches', 0)
        rate = analysis.get('validity_rate', 0)
        additions = analysis.get('total_additions', 0)
        deletions = analysis.get('total_deletions', 0)
        files = analysis.get('total_files_changed', 0)
        
        print(f"\n  🤖 {model} ({injection}):")
        print(f"     • Patches: {valid}/{patches} ({rate:.1f}% valid)")
        print(f"     • Changes: +{additions} additions, -{deletions} deletions")
        print(f"     • Files modified: {files}")
        
        # Show common issues if any
        issues = analysis.get('common_issues', {})
        if issues:
            print(f"     • Issues: {', '.join(f'{k} ({v})' for k, v in issues.items())}")
        else:
            print(f"     • Issues: None ✅")
    
    # Performance summary
    print(f"\n⚡ PERFORMANCE SUMMARY:")
    if results.get('total_valid_patches', 0) > 0:
        print(f"  • All patches are properly formatted ✅")
        print(f"  • Ready for SWE-bench testing ✅")
    else:
        print(f"  • No valid patches generated ❌")
    
    # Timestamp
    timestamp = results.get('timestamp', 'Unknown')
    print(f"\n🕒 Analysis completed: {timestamp}")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Run full SWE-bench pipeline")
    parser.add_argument("--limit", type=int, default=5,
                       help="Number of samples per model/injection combination")
    parser.add_argument("--skip-clear", action="store_true",
                       help="Skip clearing results directories")
    parser.add_argument("--skip-gen", action="store_true",
                       help="Skip generation step")
    parser.add_argument("--skip-eval", action="store_true",
                       help="Skip evaluation step")
    parser.add_argument("--real-eval", action="store_true",
                       help="Run real SWE-bench test evaluation (requires proper setup)")
    parser.add_argument("--gen-dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_gen",
                       help="Generation pipeline directory")
    parser.add_argument("--eval-dir",
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval", 
                       help="Evaluation pipeline directory")

    args = parser.parse_args()
    
    gen_dir = Path(args.gen_dir)
    eval_dir = Path(args.eval_dir)
    
    print("🚀 Starting Full SWE-bench Pipeline")
    print(f"Generation directory: {gen_dir}")
    print(f"Evaluation directory: {eval_dir}")
    print(f"Sample limit: {args.limit}")
    
    # Step 1: Clear results (unless skipped)
    if not args.skip_clear:
        if not clear_results(gen_dir / "results", eval_dir / "results"):
            print("❌ Failed to clear results")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping clear results step")
    
    # Step 2: Run generation (unless skipped)
    if not args.skip_gen:
        if not run_generation(gen_dir, args.limit):
            print("❌ Generation failed")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping generation step")
    
    # Step 3: Run evaluation (unless skipped)
    if not args.skip_eval:
        if args.real_eval:
            if not run_real_evaluation(eval_dir):
                print("❌ Real evaluation failed")
                sys.exit(1)
        else:
            if not run_evaluation(eval_dir):
                print("❌ Evaluation failed")
                sys.exit(1)
    else:
        print("\n⏭️  Skipping evaluation step")
    
    # Step 4: Load and print results
    print("\n📊 Loading evaluation results...")
    results = load_evaluation_results(eval_dir)
    print_metrics(results)
    
    print("\n✅ Full pipeline completed successfully!")

if __name__ == "__main__":
    main()
