# SWE-Bench Model Evaluation Pipeline

<p align="center">
  <img src="docs/assets/swebench_banner.svg" style="height: 10em" alt="SWE-Bench Evaluation" />
</p>

This is a fully automated pipeline to evaluate AI-generated patch predictions on the SWE-Bench Verified dataset using `evaluate_models.py`. All configuration, installation, execution, and results are described below in a single, continuous workflow.

---

## Configuration and Setup

All paths and parameters are set directly in `evaluate_models.py`. You can edit them as needed:

PREDICTIONS_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_gen/results/gpt-oss-120b/malicious_import_20250923_164813.jsonl"  
RUN_ID = "talha_test_self_patch_files"  
OUTPUT_DIR = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/results"  
EVALUATION_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/logs/run_evaluation"  
SAVE_OUTPUT_PATH = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/"  
DATASET_NAME = "princeton-nlp/SWE-bench_Verified"  
SPLIT = "test"  
MAX_WORKERS = 4  

No environment variables are required; all paths are hard-coded for simplicity.

---

## Installation & Running the Pipeline

Run all steps in a single terminal session on your Linux machine. Copy and paste the following directly:

cd ~/vibe-coding/pipeline/swebench_eval_talha/  
./install_docker.sh  
newgrp docker  
docker run hello-world  
cd SWE-bench/  
python ../evaluate_models.py  

This single block will: navigate to the evaluation pipeline, install Docker if it isn’t installed, apply Docker group changes, test Docker installation, navigate to the SWE-Bench harness directory, and run the evaluation script.

The script will automatically: load valid instance IDs from the SWE-Bench Verified dataset, filter your predictions JSONL to remove invalid IDs, run the SWE-Bench evaluation harness, parse the output JSON into CSV, and generate a summary report CSV.

---

## Outputs

After running the script, you will find the following:

Filtered Predictions JSON: `filtered_<original_predictions_file>.jsonl` located in the same folder as your original predictions. Contains only valid IDs for evaluation.

Full Evaluation CSV: `results/evaluation_full_<injection_type>_<datetime>.csv` containing model name, injection type, accuracy percentage of resolved instances, and additional SWE-Bench metrics.

Summary Report CSV: `results/report_summary_<injection_type>_<datetime>.csv` which aggregates evaluation reports for quick inspection.

Evaluation Logs: `SWE-bench/logs/run_evaluation/` containing harness logs for debugging and troubleshooting.

---

## Viewing Results

All CSV outputs can be found in the `results` folder. Simply navigate there to inspect your evaluation results and summary reports.

--

## Workflow Overview

Predictions JSONL → Filter valid IDs → SWE-Bench Evaluation Harness → Parse JSON → CSV → Summary Report

---

## Citation & License

MIT License.  

@misc{talha2025swebench_eval,
    title={SWE-Bench Model Evaluation Pipeline},
    author={Muhammad Talha},
    year={2025},
    url={https://github.com/Talha1818/swebench_eval_talha}
}
