import json
import pandas as pd
import subprocess
import os
from datasets import load_dataset
from pathlib import Path

from generate_csv import collect_and_count_reports

# Paths
# PREDICTIONS_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_gen/results_20_system/gpt-oss-120b/arbitrary_payload_20250922_014712.jsonl"

PREDICTIONS_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_gen/results/gpt-oss-120b/malicious_import_20250923_164813.jsonl"
RUN_ID = "talha_test_self_patch_files"


OUTPUT_DIR = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/results"
EVALUATION_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/logs/run_evaluation"

SAVE_OUTPUT_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/"

# Dataset params
DATASET_NAME = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
MAX_WORKERS = 4

def load_valid_ids():
    """Load the SWE-bench dataset and return a set of valid instance IDs."""
    dataset = load_dataset(DATASET_NAME, split=SPLIT)
    return set(dataset["instance_id"])


def filter_predictions(pred_path, valid_ids):
    filtered_path = str(Path(pred_path).with_name("filtered_" + Path(pred_path).name))
    with open(pred_path) as f_in, open(filtered_path, "w") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print("Skipping invalid JSON line:", line)
                continue
            if item.get("instance_id") in valid_ids:
                f_out.write(json.dumps(item) + "\n")
    return filtered_path


def run_evaluation(pred_path, run_id):
    """Run SWE-bench evaluation."""
    cmd = [
        "python", "-m", "swebench.harness.run_evaluation",
        "--predictions_path", str(pred_path),
        "--max_workers", str(MAX_WORKERS),
        "--run_id", run_id,
        "--dataset_name", DATASET_NAME,
        "--split", SPLIT
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=False)
    return f"{run_id}.json"

def parse_results(json_file, model_name):
    if not os.path.exists(json_file):
        print(f"⚠️ JSON file not found: {json_file}")
        return None
    with open(json_file) as f:
        data = json.load(f)
    df = pd.DataFrame([data])
    df['model'] = model_name
    df['injection_type'] = os.path.splitext(os.path.basename(json_file))[0]
    df['accuracy'] = df.apply(
        lambda row: round((row.get('submitted_instances', 0) and row.get('resolved_instances', 0) / row['submitted_instances']) * 100, 2)
        if row.get('submitted_instances', 0) > 0 else 0, axis=1
    )
    # Reorder columns
    cols = ['model', 'injection_type', 'accuracy'] + [c for c in df.columns if c not in ['model', 'injection_type', 'accuracy']]
    return df[cols]

# def main():
#     # Load valid dataset IDs
#     valid_ids = load_valid_ids()

#     # Filter predictions to remove missing IDs
#     filtered_pred_path = filter_predictions(PREDICTIONS_PATH, valid_ids)

#     # Check if any instances exist in filtered predictions
#     if not filtered_pred_path or os.path.getsize(filtered_pred_path) == 0:
#         print("⚠️ No valid instances found in filtered predictions. Skipping evaluation.")
#         return

#     # Run evaluation on filtered predictions
#     try:
#         result_json = run_evaluation(filtered_pred_path, RUN_ID)
#     except IndexError:
#         print("❌ Evaluation failed: no instances were processed. Exiting.")
#         return

#     print("Result JSON file:", result_json)

#     # Construct full JSON path
#     JSON_PATH = os.path.join(SAVE_OUTPUT_PATH, f"gpt-oss-120b.{result_json}")
#     print("JSON_PATH:", JSON_PATH)

#     # Parse results into DataFrame
#     df = parse_results(JSON_PATH, "gpt-oss-120b")

#     if df is not None and not df.empty:
#         os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
#         df.to_csv(OUTPUT_CSV, index=False)
#         print(f"✅ Full results written to {OUTPUT_CSV}")
#         print(df.head())
#     else:
#         print("⚠️ No results to write, DataFrame is empty.")

def get_model_and_injection(path: str):
    """Extract model name, injection type, and datetime from predictions path."""
    model_name = os.path.basename(os.path.dirname(path))  # gpt-oss-120b
    injection_type = os.path.splitext(os.path.basename(path))[0]  # malicious_import_20250923_164813
    
    # Extract datetime if present (last part after last "_")
    datetime_str = injection_type.split("_")[-1] if "_" in injection_type else "na"
    return model_name, injection_type, datetime_str

def main():
    # Load valid dataset IDs
    valid_ids = load_valid_ids()

    # Filter predictions to remove missing IDs
    filtered_pred_path = filter_predictions(PREDICTIONS_PATH, valid_ids)

    if not filtered_pred_path or os.path.getsize(filtered_pred_path) == 0:
        print("⚠️ No valid instances found in filtered predictions. Skipping evaluation.")
        return

    # Extract model + injection type + datetime
    model_name, injection_type, datetime_str = get_model_and_injection(PREDICTIONS_PATH)

    # Run evaluation
    try:
        result_json = run_evaluation(filtered_pred_path, RUN_ID)
    except IndexError:
        print("❌ Evaluation failed: no instances were processed. Exiting.")
        return

    print("Result JSON file:", result_json)

    # Construct full JSON path
    JSON_PATH = os.path.join(SAVE_OUTPUT_PATH, f"{model_name}.{result_json}")
    print("JSON_PATH:", JSON_PATH)

    # Parse results into DataFrame
    df = parse_results(JSON_PATH, model_name)

    if df is not None and not df.empty:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Save evaluation results with injection type + datetime
        eval_csv = os.path.join(OUTPUT_DIR, f"evaluation_full_{injection_type}_{datetime_str}.csv")
        df.to_csv(eval_csv, index=False)
        print(f"✅ Full results written to {eval_csv}")
        print(df.head())
    else:
        print("⚠️ No results to write, DataFrame is empty.")

    # Collect report.json summary for all models
    report_csv = os.path.join(OUTPUT_DIR, f"report_summary_{injection_type}_{datetime_str}.csv")
    report_df = collect_and_count_reports(EVALUATION_PATH, report_csv)

    if report_df is not None and not report_df.empty:
        print(f"✅ Report summary written to {report_csv}")
        print(report_df.head())
    else:
        print("⚠️ No report.json summary generated.")

if __name__ == "__main__":
    main()
