from __future__ import annotations
import os
from typing import List, Dict, Any
from datasets import load_dataset


# Which split to use: "SWE-bench_Lite", "SWE-bench_Verified", or "SWE-bench"
DEFAULT_SPLIT = os.environ.get("SWE_SPLIT", "test")


REPO_ID = "princeton-nlp/SWE-bench"


def load_swebench_split(split: str | None = None) -> List[Dict]:
    """Load a SWE-bench split and return a list of simple dict samples.
    Each sample carries the fields needed by the prompt & scorer.
    """
    split = split or DEFAULT_SPLIT
    ds = load_dataset(REPO_ID, split=split)
    out: List[Dict] = []
    for ex in ds:
        out.append({
            "instance_id": ex["instance_id"],
            "repo": ex["repo"],
            "title": ex.get("title", ""),
            "problem_statement": ex.get("problem_statement", ""),
            # Keep raw around in case you want richer prompting later
            "_raw": ex,
        })
    return out