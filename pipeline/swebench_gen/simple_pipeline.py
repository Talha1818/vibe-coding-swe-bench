#!/usr/bin/env python3
"""
Simple pipeline that runs generation with JSON logs and extracts raw patches.
"""
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def run_generation_parallel(models: List[str], limit: int = 5, injection_type: str = "none") -> bool:
    """Run generation for multiple models in parallel using inspect-ai's built-in parallelization."""
    
    # Set environment variables
    env = os.environ.copy()
    env["PATH"] = "/root/vibe-code/bin:/miniconda3/bin:" + env.get("PATH", "")
    env["OPENROUTER_API_KEY"] = "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"
    env["INSPECT_LOG_FORMAT"] = "json"  # Use JSON logs instead of ZIP
    if injection_type != "none":
        env["PROMPT_INJECTION_TYPE"] = injection_type
    
    print(f"🔄 Running generation for {len(models)} models in parallel with injection: {injection_type}")
    print(f"Models: {models}")
    
    # Build command with multiple models - inspect-ai handles parallelization internally
    cmd = [
        "inspect", "eval", "task.py@swebench_generate",
        "--model-base-url", "https://openrouter.ai/api/v1",
        "-M", "api_key=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",
        "--limit", str(limit)
    ]
    
    # Add each model to the command
    for model in models:
        cmd.extend(["--model", model])
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"❌ Error running generation: {result.stderr}")
        return False
    
    print(f"✅ Generation completed for {len(models)} models")
    return True

def extract_raw_patches_from_json_logs(log_dir: str = "logs") -> List[Dict[str, Any]]:
    """Extract raw patches from JSON log files."""
    
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"No logs directory found at {log_dir}")
        return []
    
    # Find all JSON log files
    log_files = list(log_path.glob("*.json"))
    
    if not log_files:
        print(f"No JSON log files found in {log_dir}")
        return []
    
    print(f"Found {len(log_files)} JSON log files")
    
    patches = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            # Extract patches from the log data
            if 'samples' in log_data:
                for sample in log_data['samples']:
                    if 'output' in sample and 'completion' in sample['output']:
                        patch_content = sample['output']['completion']
                        instance_id = sample.get('id', 'unknown')
                        model_name = sample['output'].get('model', 'openrouter')
                        
                        # Keep the raw patch content - no cleaning!
                        patches.append({
                            "instance_id": instance_id,
                            "model_name_or_path": model_name,
                            "model_patch": patch_content  # Raw, unmodified
                        })
                        
        except Exception as e:
            print(f"Error processing {log_file.name}: {e}")
            continue
    
    return patches

def save_raw_patches(patches: List[Dict[str, Any]], output_dir: str = "results"):
    """Save raw patches to model-specific directories with injection type and timestamp."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Group patches by model
    model_patches = {}
    for patch in patches:
        model_name = patch.get('model_name_or_path', 'unknown')
        model_dir_name = model_name.replace('/', '_').replace(':', '_')
        
        if model_dir_name not in model_patches:
            model_patches[model_dir_name] = []
        model_patches[model_dir_name].append(patch)
    
    # Save patches for each model
    for model_name, model_patch_list in model_patches.items():
        model_dir = output_path / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with injection type and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"none_{timestamp}.jsonl"
        output_file = model_dir / filename
        
        # Save patches for this model
        with open(output_file, 'w') as f:
            for patch in model_patch_list:
                f.write(json.dumps(patch) + '\n')
        
        print(f"💾 Saved {len(model_patch_list)} raw patches for {model_name} to {output_file}")

def main():
    """Main pipeline function."""
    
    print("🚀 Starting simple SWE-bench pipeline with parallel model execution")
    
    # Configuration
    models = ["openai/openai/gpt-4o", "openai/openai/gpt-4o-mini"]
    injection_types = ["none", "arbitrary_payload"]
    limit = 3
    
    # Run generation for each injection type with all models in parallel
    for injection_type in injection_types:
        print(f"\n🔄 Running generation for injection type: {injection_type}")
        success = run_generation_parallel(models, limit, injection_type)
        if not success:
            print(f"⚠️ Skipping injection type {injection_type} due to generation failure")
            continue
    
    print("\n📊 Extracting raw patches from JSON logs...")
    
    # Extract raw patches from JSON log files
    patches = extract_raw_patches_from_json_logs()
    
    if patches:
        print(f"Found {len(patches)} raw patches")
        
        # Save patches to model-specific directories
        save_raw_patches(patches)
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📈 Generated {len(patches)} raw patches across {len(set(p['model_name_or_path'] for p in patches))} models")
        print(f"📁 Patches saved to results/model_name/injection_timestamp.jsonl")
    else:
        print("❌ No patches found")

if __name__ == "__main__":
    main()
