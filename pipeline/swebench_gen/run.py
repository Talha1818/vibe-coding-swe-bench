#!/usr/bin/env python3
import os
import json
from pathlib import Path
from inspect_ai import eval_set, eval
from task import swebench_generate
from dotenv import load_dotenv
import uuid
from inspect_ai.model import get_model

load_dotenv()

# ---- CONFIG ----
EVALUATION_MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-3.5-turbo",
]
LIMIT_N = 2  # matches your task dataset limit
LOG_DIR = Path(__file__).parent / "logs"
PROMPT_INJECTIONS = [
    "none",
    "arbitrary_payload", 
    "bad_instructions",
]

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

def run_evaluation_for_model(eval_models:list, injection_type:str="none"):
    print(f"\n{'='*60}")
    print(f"🔬 Running experiment with model: {eval_models}")
    print(f"🔬 Injection type: {injection_type}")
    print(f"{'='*60}")

    try:
        # Set injection type environment variable
        if injection_type != "none":
            os.environ["PROMPT_INJECTION_TYPE"] = injection_type
        elif "PROMPT_INJECTION_TYPE" in os.environ:
            del os.environ["PROMPT_INJECTION_TYPE"]
        
        # Unique task ID and log dir
        unique_task_id = str(uuid.uuid4())
        unique_log_dir = LOG_DIR / f"{eval_models[0].split('/')[-1]}_{injection_type}_{unique_task_id}"
        unique_log_dir.mkdir(parents=True, exist_ok=True)

        # Create the task instance with solver models
        task_instance = swebench_generate(limit_n=LIMIT_N)

        # success, logs = eval_set(
        #     tasks=[task_instance],
        #     model=[model_id],
        #     log_dir=str(unique_log_dir),
        #     retry_on_error=3,
        #     fail_on_error=0.2,
        # )

        results = eval(
            tasks=[task_instance],
            # model=[model_id],
            model= eval_models,
            max_workers=min(len(eval_models), 4),  # Limit concurrent workers.
            log_dir=str(unique_log_dir),
            retry_on_error=3,
            fail_on_error=0.2,
            model_base_url="https://openrouter.ai/api/v1",
            model_args={"api_key": os.environ.get("OPENROUTER_API_KEY")},
            model_args_override={"api_key": os.environ.get("OPENROUTER_API_KEY")},
        )

        print(results)

        # Save results to JSONL files
        save_results_to_jsonl(results, eval_models, injection_type)

                # Process results for each model
        if hasattr(results, 'samples') and results.samples:
            # Single result object (if only one model)
            model_results = [results]
        else:
            # Multiple result objects (one per model)
            model_results = list(results) if hasattr(results, '__iter__') else [results]

    except Exception as e:
        print(f"❌ Error during evaluation for model {eval_models[0]}: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ Skipping this model and continuing with next...")

def main():
    LOG_DIR.mkdir(exist_ok=True)
    
    # Run evaluation for each injection type
    for injection_type in PROMPT_INJECTIONS:
        print(f"\n🚀 Starting evaluation with injection type: {injection_type}")
        run_evaluation_for_model(EVALUATION_MODELS, injection_type)
        print(f"✅ Completed evaluation for injection type: {injection_type}")
    
    print(f"\n🎉 All evaluations completed! Check results/ directory for output files.")

if __name__ == "__main__":
    main()
