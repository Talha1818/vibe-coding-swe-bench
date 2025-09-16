#!/usr/bin/env python3
"""
Quick test script for prompt injection attacks.
Tests a single model with a single injection type for rapid iteration.
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

def test_injection(model: str, injection_type: str, limit: int = 5):
    """Test a single model with a single injection type."""
    
    print(f"Testing {model} with injection: {injection_type}")
    
    # Create results directory
    model_id = model.replace("/", "_").replace("-", "_")
    results_dir = Path("results") / model_id
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped results file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"{model_id}_{timestamp}.json"
    
    # Prepare environment
    env = os.environ.copy()
    env.setdefault("SWE_SPLIT", "test")
    env.setdefault("PRED_PATH", str(results_file))
    
    if injection_type != "none":
        env.setdefault("PROMPT_INJECTION_TYPE", injection_type)
    
    # OpenRouter config
    base_url = "https://openrouter.ai/api/v1"
    api_key = env.get("OPENROUTER_API_KEY", "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")
    if not api_key:
        print("Error: Please export OPENROUTER_API_KEY first.")
        return
    
    model_args = ",".join([
        f"base_url={base_url}",
        f"api_key={api_key}",
        f"model={model}",
    ])
    
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
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Results will be saved to: {results_file}")
    
    try:
        # Run the model
        result = subprocess.run(cmd, env=env, check=True)
        
        # Load and display results
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = [json.loads(line) for line in f if line.strip()]
            
            print(f"\n✅ Success! Generated {len(results)} patches")
            print(f"Results saved to: {results_file}")
            
            # Show first result as example
            if results:
                print(f"\nFirst result example:")
                print(f"Sample ID: {results[0].get('instance_id', 'N/A')}")
                print(f"Model: {results[0].get('model_name_or_path', 'N/A')}")
                patch_preview = results[0].get('model_patch', '')[:200]
                print(f"Patch preview: {patch_preview}...")
        else:
            print("❌ No results file created")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_injection.py <model> <injection_type> [limit]")
        print("\nExample:")
        print("python test_injection.py openai/gpt-4o-mini arbitrary_payload 5")
        print("\nAvailable injection types:")
        print("- none (baseline)")
        print("- arbitrary_payload")
        print("- bad_instructions")
        print("- backdoor")
        print("- malicious_import")
        print("- data_exfiltration")
        print("- code_obfuscation")
        sys.exit(1)
    
    model = sys.argv[1]
    injection_type = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    test_injection(model, injection_type, limit)
