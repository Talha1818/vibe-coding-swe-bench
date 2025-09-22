#!/usr/bin/env python3
import os
from pathlib import Path
from inspect_ai import eval_set, eval
from task import swebench_generate
from scorer import save_results_to_jsonl
from dotenv import load_dotenv
import uuid
from inspect_ai.model import get_model

load_dotenv()

# ---- CONFIG ----
EVALUATION_MODELS = [
    "openrouter/openai/gpt-5",
    "openrouter/openai/gpt-oss-120b", 
    "openrouter/anthropic/claude-opus-4.1",
]
LIMIT_N = 200  # matches your task dataset limit
LOG_DIR = Path(__file__).parent / "logs"
PROMPT_INJECTIONS = [
    # "none",
    "self_delete",  # Attempts to make the model add a self-destructive command that deletes the current directory
    "evil_package",  # Tries to get the model to install a malicious package via pip
    "curl_bash",  # Attempts to make the model execute a malicious curl command
    "eval_injection",  # Tries to get the model to add an unsafe eval function
     "arbitrary_payload", 
    "bad_instructions",
    "malicious_import"
]

def run_evaluation_for_model(eval_models:list, injection_type:str="none"):
    print(f"\n{'='*60}")
    print(f"🔬 Running experiment with model: {eval_models}")
    print(f"🔬 Injection type: {injection_type}")
    print(f"{'='*60}")

    try:
        # Set injection type environment variable BEFORE creating the task
        if injection_type != "none":
            os.environ["PROMPT_INJECTION_TYPE"] = injection_type
        elif "PROMPT_INJECTION_TYPE" in os.environ:
            del os.environ["PROMPT_INJECTION_TYPE"]
        
        # Unique task ID and log dir
        unique_task_id = str(uuid.uuid4())
        unique_log_dir = LOG_DIR / f"{eval_models[0].split('/')[-1]}_{injection_type}_{unique_task_id}"
        unique_log_dir.mkdir(parents=True, exist_ok=True)

        # Create the task instance AFTER setting the environment variable
        # This ensures the prompt injection is applied during dataset loading
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
        )

        print(results)

        # Save results to JSONL files
        save_results_to_jsonl(results, eval_models, injection_type)

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
