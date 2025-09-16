#!/usr/bin/env python3
"""
Parallel model runner using inspect-ai's built-in parallel execution.
Runs multiple models and injection types in parallel using inspect-ai's capabilities.
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def extract_patches_from_log(log_file: Path) -> List[Dict[str, Any]]:
    """Extract patches from a single log file."""
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    patches = []
    
    # Extract samples from the log
    if 'samples' in log_data:
        for sample in log_data['samples']:
            # Get the instance_id from the sample
            instance_id = sample.get('id', 'unknown')
            
            # Extract the patch from the assistant's message
            patch_content = ""
            if 'messages' in sample:
                for message in sample['messages']:
                    if message.get('role') == 'assistant' and 'content' in message:
                        content = message['content']
                        # Extract diff content from code blocks
                        if '```diff' in content:
                            # Extract everything between ```diff and ```
                            start = content.find('```diff') + 7
                            end = content.find('```', start)
                            if end > start:
                                patch_content = content[start:end].strip()
                        elif content.strip().startswith('diff --git'):
                            # Direct diff content
                            patch_content = content.strip()
            
            if patch_content:
                patches.append({
                    "instance_id": instance_id,
                    "model_name_or_path": "openrouter",
                    "model_patch": patch_content
                })
    
    return patches

def run_single_model_injection(
    model: str,
    injection_type: str,
    split: str = "test",
    limit: int = 10,
    results_base_dir: Path = None
) -> Dict[str, Any]:
    """Run a single model with a specific injection type."""
    if results_base_dir is None:
        results_base_dir = Path("results")
    
    # Create model-specific directory
    model_id = model.replace("/", "_").replace("-", "_")
    model_dir = results_base_dir / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped results file with injection type
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    injection_suffix = f"_{injection_type}" if injection_type != "none" else ""
    results_file = model_dir / f"{model_id}{injection_suffix}_{timestamp}.json"
    
    # Prepare environment
    env = os.environ.copy()
    env.setdefault("SWE_SPLIT", split)
    env.setdefault("PRED_PATH", str(results_file))
    
    if injection_type != "none":
        env.setdefault("PROMPT_INJECTION_TYPE", injection_type)
    
    # OpenRouter config
    base_url = "https://openrouter.ai/api/v1"
    api_key = env.get("OPENROUTER_API_KEY", "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")
    if not api_key:
        raise SystemExit("Please export OPENROUTER_API_KEY first.")
    
    # Set environment variables for OpenRouter
    env["OPENAI_API_KEY"] = api_key
    env["OPENAI_BASE_URL"] = base_url
    
    # Build command
    cmd = [
        "inspect", "eval", "task.py@swebench_generate",
        "--model", f"openai/{model}",
        "--model-base-url", base_url,
        "-M", f"api_key={api_key}",
        "--limit", str(limit)
    ]
    
    print(f"Running {model} with injection: {injection_type}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run the model
        result = subprocess.run(cmd, env=env, check=True)
        
        # Extract patches from the most recent log file
        log_files = list(Path("logs").glob("*.json"))
        if log_files:
            # Get the most recent log file
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            patches = extract_patches_from_log(latest_log)
            
            # Save patches to the expected results file
            with open(results_file, 'w') as f:
                for patch in patches:
                    f.write(json.dumps(patch) + "\n")
        else:
            patches = []
        
        return {
            "model": model,
            "injection_type": injection_type,
            "split": split,
            "limit": limit,
            "timestamp": timestamp,
            "results_file": str(results_file),
            "num_results": len(patches),
            "success": True,
            "error": None
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "model": model,
            "injection_type": injection_type,
            "split": split,
            "limit": limit,
            "timestamp": timestamp,
            "results_file": str(results_file),
            "num_results": 0,
            "success": False,
            "error": str(e)
        }

def run_parallel_models(
    models: List[str],
    injection_types: List[str],
    split: str = "test",
    limit: int = 10,
    results_base_dir: Path = None
) -> List[Dict[str, Any]]:
    """Run all models and injection types in parallel using subprocess."""
    if results_base_dir is None:
        results_base_dir = Path("results")
    
    results_base_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    total_combinations = len(models) * len(injection_types)
    current = 0
    
    print(f"Running {total_combinations} combinations in parallel...")
    
    # Create all combinations
    combinations = []
    for model in models:
        for injection_type in injection_types:
            combinations.append((model, injection_type))
    
    # Run all combinations in parallel using subprocess
    processes = []
    for model, injection_type in combinations:
        current += 1
        print(f"\n[{current}/{total_combinations}] Starting {model} with {injection_type}")
        
        # Start each model/injection combination as a separate process
        cmd = [
            "python", "-c", f"""
import sys
import os
sys.path.append('.')
from parallel_model_runner import run_single_model_injection
import json
from pathlib import Path

# Set up environment
os.environ['OPENROUTER_API_KEY'] = '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'

result = run_single_model_injection(
    model='{model}',
    injection_type='{injection_type}',
    split='{split}',
    limit={limit},
    results_base_dir=Path('{results_base_dir}')
)
print(json.dumps(result))
"""
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append((process, model, injection_type))
    
    # Wait for all processes to complete and collect results
    for process, model, injection_type in processes:
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            try:
                result = json.loads(stdout.decode())
                all_results.append(result)
                print(f"✅ {model} with {injection_type}: SUCCESS ({result.get('num_results', 0)} patches)")
            except json.JSONDecodeError as e:
                print(f"❌ {model} with {injection_type}: Failed to parse result - {e}")
                print(f"Output: {stdout.decode()}")
                all_results.append({
                    "model": model,
                    "injection_type": injection_type,
                    "success": False,
                    "num_results": 0,
                    "error": "Failed to parse result"
                })
        else:
            print(f"❌ {model} with {injection_type}: FAILED")
            print(f"Error: {stderr.decode()}")
            all_results.append({
                "model": model,
                "injection_type": injection_type,
                "success": False,
                "num_results": 0,
                "error": stderr.decode()
            })
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Parallel multi-model prompt injection testing")
    parser.add_argument("--models", nargs="+", 
                       default=["openai/gpt-4o", "openai/gpt-4o-mini"], 
                       help="Models to test")
    parser.add_argument("--injections", nargs="+", 
                       default=["none", "arbitrary_payload"], 
                       help="Injection types to test")
    parser.add_argument("--split", default="test", help="SWE-bench split")
    parser.add_argument("--limit", type=int, default=10, help="Number of samples per run")
    parser.add_argument("--results_dir", default="results", help="Base results directory")

    args = parser.parse_args()

    results_base_dir = Path(args.results_dir)
    results_base_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Starting parallel evaluation...")
    print(f"Models: {args.models}")
    print(f"Injection types: {args.injections}")
    print(f"Limit: {args.limit}")

    final_results = run_parallel_models(
        models=args.models,
        injection_types=args.injections,
        split=args.split,
        limit=args.limit,
        results_base_dir=results_base_dir
    )

    # Save final summary
    summary_file = results_base_dir / "parallel_experiment_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print("\n✅ All experiments completed!")
    print(f"Results saved to: {results_base_dir}")
    print(f"Summary: {summary_file}")
    
    successful_runs = sum(1 for r in final_results if r.get('success', False))
    total_patches = sum(r.get('num_results', 0) for r in final_results)
    print(f"Successful runs: {successful_runs}/{len(final_results)}")
    print(f"Total patches generated: {total_patches}")

if __name__ == "__main__":
    main()
