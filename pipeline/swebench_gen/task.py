from __future__ import annotations
import os
from inspect_ai import task, Task
from inspect_ai.solver import generate
from dataset import load_swebench_samples
from scorer import swebench_patch_scorer

@task
def swebench_generate(limit_n: int = None) -> Task:
    """SWE-bench generation task with prompt injection support."""
    
    # Load data with limit if provided
    limit = limit_n if limit_n is not None else int(os.environ.get("SWE_LIMIT", "10"))
    data = load_swebench_samples(os.environ.get("SWE_SPLIT", "test"), limit)
    
    # Use simple generate without template since input is already complete
    solver = generate()
    
    return Task(
        dataset=data,
        solver=solver,
    )