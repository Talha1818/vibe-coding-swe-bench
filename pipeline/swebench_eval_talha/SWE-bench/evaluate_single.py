import subprocess
import json
import os
import pandas as pd
from pathlib import Path

# Paths
PREDICTIONS_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_gen/results_20_system/gpt-5/arbitrary_payload_20250922_014712_predictions.jsonl"

RUN_ID = "talha_test_single"
OUTPUT_CSV = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/results/evaluation_single_full.csv"

SAVE_OUTPUT_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/"

# Dataset params
DATASET_NAME = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
MAX_WORKERS = 2

def run_evaluation(pred_path, run_id):
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

def parse_results(json_file, model_name, pred_path):
    if not os.path.exists(json_file):
        return None

    with open(json_file) as f:
        data = json.load(f)

    # Convert JSON to DataFrame
    df = pd.DataFrame([data])

    # Add model, sample_id, injection_type
    df['model'] = model_name
    # df['sample_id'] = os.path.basename(pred_path)
    df['injection_type'] = os.path.splitext(os.path.basename(pred_path))[0]

    # Compute accuracy
    df['accuracy'] = df.apply(
        lambda row: round((row.get('submitted_instances', 0) and row.get('resolved_instances', 0) / row['submitted_instances']) * 100, 2) 
        if row.get('submitted_instances', 0) > 0 else 0, axis=1
    )

    # Reorder columns: model, sample_id, injection_type, accuracy, then rest
    cols = ['model','injection_type', 'accuracy'] + \
           [c for c in df.columns if c not in ['model', 'sample_id', 'injection_type', 'accuracy']]
    df = df[cols]

    return df

def main():
    # Run evaluation
    result_json = run_evaluation(PREDICTIONS_PATH, RUN_ID)
    print("Result JSON file:", result_json)

    JSON_PATH = SAVE_OUTPUT_PATH + "gpt-5."+result_json
    print("JSON_PATH:",JSON_PATH)

    # Parse results into DataFrame
    df = parse_results(JSON_PATH, "gpt-5", PREDICTIONS_PATH)

    if df is not None:
        # Save to CSV
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ Full results written to {OUTPUT_CSV}")
        print(df.head())

if __name__ == "__main__":
    main()
