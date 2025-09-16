#!/usr/bin/env python3
"""
Extract patches from inspect-ai log files and save them to the expected result files.
This script processes the log files and creates the individual result files that the
multi_model_runner expects.
"""

import json
import os
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

def process_logs_and_save_results(logs_dir: Path, results_dir: Path):
    """Process all log files and save results to the expected locations."""
    
    # Find all log files
    log_files = list(logs_dir.glob("*.json"))
    
    # Group log files by model and injection type based on filename
    # Format: 2025-09-16T00-00-21-07-00_swebench-generate_<hash>.json
    model_injection_map = {}
    
    for log_file in log_files:
        # Extract timestamp and hash from filename
        parts = log_file.stem.split('_')
        if len(parts) >= 3:
            timestamp = parts[0] + '_' + parts[1]
            hash_part = parts[2]
            
            # We need to map this back to the model and injection type
            # This is a bit tricky since we don't have that info in the filename
            # For now, let's process all logs and create generic results
            
            patches = extract_patches_from_log(log_file)
            
            if patches:
                # Create a generic result file
                result_file = results_dir / f"extracted_patches_{timestamp}.jsonl"
                with open(result_file, 'w') as f:
                    for patch in patches:
                        f.write(json.dumps(patch) + '\n')
                
                print(f"Extracted {len(patches)} patches from {log_file.name} -> {result_file}")

def main():
    logs_dir = Path("logs")
    results_dir = Path("results")
    
    if not logs_dir.exists():
        print("No logs directory found")
        return
    
    # Create results directory if it doesn't exist
    results_dir.mkdir(exist_ok=True)
    
    # Process all log files
    process_logs_and_save_results(logs_dir, results_dir)
    
    print("Patch extraction completed!")

if __name__ == "__main__":
    main()
