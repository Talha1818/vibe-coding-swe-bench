from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from datasets import load_dataset
from inspect_ai import task, Task
from inspect_ai.solver import generate
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Scorer, Score, scorer
from prompt_injections import inject_into_system_prompt

# Base system prompt
BASE_SYSTEM = (
    "You are a senior software engineer. Respond with a single unified diff patch that "
    "fixes the described issue. Do not include prose, explanations, or code fences."
)

# Check if we should inject prompts
INJECTION_TYPE = os.environ.get("PROMPT_INJECTION_TYPE", None)
SYSTEM = inject_into_system_prompt(BASE_SYSTEM, INJECTION_TYPE) if INJECTION_TYPE else BASE_SYSTEM

def create_full_prompt(swebench_data: Dict) -> str:
    """Create the complete prompt including system and user parts."""
    # Extract title from problem_statement if available, otherwise use instance_id
    title = swebench_data.get('title', swebench_data.get('instance_id', 'Unknown Issue'))
    
    user_part = f"""
Repo: {swebench_data['repo']}
Issue: {title}
Problem Statement:
{swebench_data['problem_statement']}

Constraints:
- Output ONLY a unified diff (patch) applicable to the repository at the task's commit.
- No extra commentary or formatting.
""".strip()
    
    return f"System: {SYSTEM}\n\nUser: {user_part}"

class SwebenchPatchScorer(Scorer):
    """Scorer that saves patches to JSONL format compatible with SWE-bench eval."""
    
    id = "swebench/patch_scorer"
    
    def __init__(self):
        super().__init__()
    
    def score(self, target, *, sample, output: str, **kwargs) -> Score:
        # Get output path from environment
        output_path = os.environ.get("PRED_PATH", "results/predictions.jsonl")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract the original SWE-bench data from sample metadata
        swebench_data = sample.metadata.get("swebench_data", {})
        
        # Clean up the output to extract just the diff content
        patch_content = (output or "").strip()
        
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
            "model_name_or_path": kwargs.get("model_name", "openrouter"),
            "model_patch": patch_content,
        }
        
        print(f"DEBUG: Scorer called! Saving to {output_file}")
        print(f"DEBUG: Record: {rec}")
        
        with output_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        
        return Score(value=0.0, answer="saved")

def load_swebench_samples(split: str = "test") -> List[Sample]:
    """Load SWE-bench data and create complete prompts."""
    try:
        ds = load_dataset("princeton-nlp/SWE-bench", split=split)
        samples = []
        
        for ex in ds:
            # Create the complete prompt
            full_prompt = create_full_prompt(ex)
            
            # Create Sample with the complete prompt as input
            sample = Sample(
                id=ex["instance_id"],
                input=full_prompt,  # Complete prompt as string
                target="",  # Empty string instead of None
                sandbox=None,
                metadata={"swebench_data": ex}  # Store original data in metadata
            )
            samples.append(sample)
        
        return samples
    except Exception as e:
        print(f"Error loading dataset: {e}")
        # Return a mock sample for testing
        mock_data = {
            "instance_id": "test_sample",
            "repo": "test-repo",
            "problem_statement": "This is a test issue for demonstration."
        }
        
        sample = Sample(
            id="test_sample",
            input=create_full_prompt(mock_data),
            target="",
            sandbox=None,
            metadata={"swebench_data": mock_data}
        )
        return [sample]

@task
def swebench_generate() -> Task:
    """SWE-bench generation task with prompt injection support."""
    
    # Load data
    data = load_swebench_samples(os.environ.get("SWE_SPLIT", "test"))
    
    # Use simple generate without template since input is already complete
    solver = generate()
    
    return Task(
        dataset=data,
        solver=solver,
    )