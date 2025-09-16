
import sys
import os
sys.path.append('/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval')

try:
    from swebench import run_evaluation, get_eval_report
    import json
    
    # Load predictions
    predictions = []
    with open('/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results/openai_gpt_4o_mini_none_predictions.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line.strip()))
    
    print(f"Loaded {len(predictions)} predictions")
    
    # Run evaluation
    results = run_evaluation(
        predictions=predictions,
        log_dir='/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results/openai_gpt_4o_mini_none',
        timeout=300,
        verbose=True
    )
    
    # Get report
    report = get_eval_report(results)
    
    # Save results
    with open('/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results/openai_gpt_4o_mini_none/evaluation_results.json', 'w') as f:
        json.dump({
            'results': results,
            'report': report
        }, f, indent=2)
    
    print("Evaluation completed successfully")
    print(f"Results: {report}")
    
except Exception as e:
    print(f"Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
