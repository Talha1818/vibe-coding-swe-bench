from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from inspect_ai.scorer import Scorer, Score


class SavePatchScorer(Scorer):
    """Capture the model's patch text and append to a JSONL file.
    Returns a dummy numeric score so Inspect AI is happy.
    """

    id = "swebench/save_patch"

    def __init__(self, output_path: str = "results/predictions.jsonl"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def score(self, target, *, sample, output: str, **kwargs) -> Score:
        # `output` is the model's text. We assume it's the unified diff patch.
        rec = {
            "instance_id": sample["instance_id"],
            "model_name_or_path": kwargs.get("model_name", "openrouter"),
            "model_patch": (output or "").strip(),
        }
        with self.output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        # Return a neutral score (we'll evaluate with SWE-bench separately)
        return Score(value=0.0, answer="saved")