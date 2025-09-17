#!/usr/bin/env python3
"""
Scorer for SWE-bench patches with JSONL output format.
"""
import os
import json
from pathlib import Path
from inspect_ai.scorer import Scorer, Score, scorer

@scorer
def swebench_patch_scorer() -> Scorer:
    """Scorer that saves patches to JSONL format compatible with SWE-bench eval."""
    
    async def score(state, target) -> Score:
        # Get output path from environment
        output_path = os.environ.get("PRED_PATH", "results/predictions.jsonl")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract the original SWE-bench data from sample metadata
        swebench_data = state.sample.metadata.get("swebench_data", {})
        
        # Clean up the output to extract just the diff content
        patch_content = (state.output.content or "").strip()
        
        # Remove code block markers if present
        if patch_content.startswith("```diff"):
            start = patch_content.find("```diff") + 7
            end = patch_content.find("```", start)
            if end > start:
                patch_content = patch_content[start:end].strip()
        elif patch_content.startswith("```"):
            start = patch_content.find("```") + 3
            end = patch_content.find("```", start)
            if end > start:
                patch_content = patch_content[start:end].strip()
        
        rec = {
            "instance_id": swebench_data.get("instance_id", "unknown"),
            "model_name_or_path": getattr(state, "model_name", "openrouter"),
            "model_patch": patch_content,
        }
        
        print(f"DEBUG: Scorer called! Saving to {output_file}")
        print(f"DEBUG: Record: {rec}")
        
        with output_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        
        return Score(value=0.0, answer="saved")
    
    return score

def save_results_to_jsonl(results, eval_models, injection_type="none"):
    """Save evaluation results to JSONL files in the results directory."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Process results for each model
    if hasattr(results, 'samples') and results.samples:
        # Single result object (if only one model)
        model_results = [results]
    else:
        # Multiple result objects (one per model)
        model_results = list(results) if hasattr(results, '__iter__') else [results]
    
    for i, result in enumerate(model_results):
        if i < len(eval_models):
            model_name = eval_models[i].split('/')[-1]
            model_dir = results_dir / model_name
            model_dir.mkdir(exist_ok=True)
            
            # Create filename with injection type and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{injection_type}_{timestamp}.jsonl"
            output_file = model_dir / filename
            
            # Save patches for this model
            with open(output_file, 'w') as f:
                for sample in result.samples:
                    if hasattr(sample, 'output') and sample.output:
                        patch_content = getattr(sample.output, 'completion', '') or getattr(sample.output, 'content', '') or ""
                        
                        # Clean up the output to extract just the diff content
                        if patch_content.startswith("```diff"):
                            start = patch_content.find("```diff") + 7
                            end = patch_content.find("```", start)
                            if end > start:
                                patch_content = patch_content[start:end].strip()
                        elif patch_content.startswith("```"):
                            start = patch_content.find("```") + 3
                            end = patch_content.find("```", start)
                            if end > start:
                                patch_content = patch_content[start:end].strip()
                        
                        # Get metadata from sample
                        swebench_data = sample.metadata.get("swebench_data", {})
                        
                        rec = {
                            "instance_id": swebench_data.get("instance_id", sample.id),
                            "model_name_or_path": model_name,
                            "model_patch": patch_content,
                        }
                        
                        f.write(json.dumps(rec) + '\n')
            
            print(f"💾 Saved results for {model_name} to {output_file}")
