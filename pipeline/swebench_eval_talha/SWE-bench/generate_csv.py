import os
import json
import pandas as pd

OUTPUT_CSV = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/results/report_summary.csv"

def collect_and_count_reports(base_path: str, output_csv: str = OUTPUT_CSV) -> pd.DataFrame:
    data = {}
    grand_total = 0

    for model_group in os.listdir(base_path):  # e.g. talha_test_self_patch_files
        model_group_path = os.path.join(base_path, model_group)
        if not os.path.isdir(model_group_path):
            continue

        print(f"\nChecking model group: {model_group}")
        group_total = 0

        # dive into sub-models (e.g. gpt-oss-120b)
        for model_name in os.listdir(model_group_path):
            model_path = os.path.join(model_group_path, model_name)
            if not os.path.isdir(model_path):
                continue

            model_total = 0

            for instance_name in os.listdir(model_path):  # e.g. astropy__astropy-7336
                instance_path = os.path.join(model_path, instance_name)
                report_file = os.path.join(instance_path, "report.json")

                if os.path.exists(report_file):
                    try:
                        with open(report_file, "r") as f:
                            report = json.load(f)

                        # Extract instance ID
                        instance_id = list(report.keys())[0]
                        tests_status = report[instance_id].get("tests_status", {})

                        # Count test cases
                        total_cases = sum(
                            len(results.get("success", [])) + len(results.get("failure", []))
                            for results in tests_status.values()
                        )
                        passed_cases = sum(len(results.get("success", [])) for results in tests_status.values())
                        failed_cases = sum(len(results.get("failure", [])) for results in tests_status.values())

                        # Build dictionary
                        report_dict = {
                            "total_test_cases": total_cases,
                            "test_cases_passed": passed_cases,
                            "test_cases_failed": failed_cases,
                            "test_case_report": report_file
                        }

                        # Insert into data
                        if instance_id not in data:
                            data[instance_id] = {}
                        data[instance_id][model_name] = report_dict

                        # Counters
                        model_total += 1
                        group_total += 1
                        grand_total += 1

                    except Exception as e:
                        print(f"⚠️ Error reading {report_file}: {e}")

            print(f"📊 report.json found in {model_total} instances for model {model_name}")

        print(f"📊 report.json found in {group_total} instances for group {model_group}")

    print(f"\n📊 Grand Total report.json files found: {grand_total}")

    # Convert results into DataFrame
    df = pd.DataFrame.from_dict(data, orient="index")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # Save to CSV
    df.to_csv(output_csv)

    print(f"✅ Report summary saved to: {output_csv}")
    return df



if __name__ == "__main__":
    base_path = "/home/ec2-user/vibe-coding/pipeline/swebench_eval_talha/SWE-bench/logs/run_evaluation"
    df = collect_and_count_reports(base_path, OUTPUT_CSV)

    print(df.head())

