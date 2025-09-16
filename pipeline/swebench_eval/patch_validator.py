#!/usr/bin/env python3
"""
Patch Validator
Validates generated patches and provides basic metrics without running full SWE-bench evaluation.
"""

from __future__ import annotations
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def load_patch_results(results_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load all patch results from the swebench_gen results directory."""
    patch_data = {}
    
    # Find all model directories
    for model_dir in results_dir.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            patch_data[model_name] = []
            
            # Load all JSON files in the model directory
            for json_file in model_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                patch_record = json.loads(line.strip())
                                patch_record['source_file'] = str(json_file)
                                patch_data[model_name].append(patch_record)
                except Exception as e:
                    print(f"Warning: Could not load {json_file}: {e}")
    
    return patch_data

def validate_patch(patch_content: str) -> Dict[str, Any]:
    """Validate a single patch and return metrics."""
    
    validation_results = {
        "is_valid_diff": False,
        "has_file_header": False,
        "has_hunk_header": False,
        "num_additions": 0,
        "num_deletions": 0,
        "num_files_changed": 0,
        "patch_length": len(patch_content),
        "issues": []
    }
    
    if not patch_content.strip():
        validation_results["issues"].append("Empty patch content")
        return validation_results
    
    # Check if it's a valid diff format
    if patch_content.startswith("diff --git") or patch_content.startswith("---") or patch_content.startswith("+++"):
        validation_results["is_valid_diff"] = True
    else:
        validation_results["issues"].append("Not a valid diff format")
    
    # Check for file headers
    if "diff --git" in patch_content:
        validation_results["has_file_header"] = True
        # Count files changed
        file_headers = re.findall(r'diff --git a/(.+) b/(.+)', patch_content)
        validation_results["num_files_changed"] = len(file_headers)
    else:
        validation_results["issues"].append("Missing diff --git header")
    
    # Check for hunk headers
    if "@@" in patch_content:
        validation_results["has_hunk_header"] = True
        # Count additions and deletions
        additions = len(re.findall(r'^\+', patch_content, re.MULTILINE))
        deletions = len(re.findall(r'^-', patch_content, re.MULTILINE))
        validation_results["num_additions"] = additions
        validation_results["num_deletions"] = deletions
    else:
        validation_results["issues"].append("Missing hunk headers (@@)")
    
    # Check for common issues
    if "```" in patch_content:
        validation_results["issues"].append("Contains markdown code blocks")
    
    if patch_content.count("\n") < 3:
        validation_results["issues"].append("Patch too short")
    
    return validation_results

def analyze_patches(patch_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a collection of patches and return aggregate metrics."""
    
    total_patches = len(patch_records)
    valid_patches = 0
    total_additions = 0
    total_deletions = 0
    total_files_changed = 0
    all_issues = []
    
    patch_analyses = []
    
    for record in patch_records:
        patch_content = record.get("model_patch", "")
        validation = validate_patch(patch_content)
        
        patch_analysis = {
            "instance_id": record.get("instance_id", "unknown"),
            "injection_type": record.get("injection_type", "unknown"),
            "validation": validation
        }
        patch_analyses.append(patch_analysis)
        
        if validation["is_valid_diff"]:
            valid_patches += 1
        
        total_additions += validation["num_additions"]
        total_deletions += validation["num_deletions"]
        total_files_changed += validation["num_files_changed"]
        all_issues.extend(validation["issues"])
    
    # Calculate aggregate metrics
    validity_rate = (valid_patches / total_patches) * 100 if total_patches > 0 else 0
    
    # Count common issues
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    return {
        "total_patches": total_patches,
        "valid_patches": valid_patches,
        "validity_rate": validity_rate,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "total_files_changed": total_files_changed,
        "avg_additions_per_patch": total_additions / total_patches if total_patches > 0 else 0,
        "avg_deletions_per_patch": total_deletions / total_patches if total_patches > 0 else 0,
        "common_issues": issue_counts,
        "patch_analyses": patch_analyses
    }

def main():
    parser = argparse.ArgumentParser(description="Validate and analyze generated patches")
    parser.add_argument("--results_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_gen/results",
                       help="Directory containing patch results")
    parser.add_argument("--output_dir", 
                       default="/Users/dipikakhullar/Desktop/vibe-coding/pipeline/swebench_eval/results",
                       help="Directory to save analysis results")
    parser.add_argument("--model", 
                       help="Specific model to analyze (default: all)")
    parser.add_argument("--injection_type", 
                       help="Specific injection type to analyze (default: all)")

    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Starting patch validation and analysis")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    
    # Load patch data
    patch_data = load_patch_results(results_dir)
    
    if not patch_data:
        print("No patch data found!")
        return
    
    print(f"Found patch data for models: {list(patch_data.keys())}")
    
    all_analyses = []
    
    for model_name, patch_records in patch_data.items():
        if args.model and model_name != args.model:
            continue
            
        print(f"\n📊 Analyzing model: {model_name}")
        print(f"Found {len(patch_records)} patch records")
        
        # Group patches by injection type
        patches_by_injection = {}
        for record in patch_records:
            injection_type = record.get("injection_type", "none")
            if args.injection_type and injection_type != args.injection_type:
                continue
                
            if injection_type not in patches_by_injection:
                patches_by_injection[injection_type] = []
            patches_by_injection[injection_type].append(record)
        
        # Analyze each injection type
        for injection_type, patches in patches_by_injection.items():
            if not patches:
                continue
                
            print(f"\n🔍 Analyzing {injection_type} injection ({len(patches)} patches)")
            
            # Analyze patches
            analysis = analyze_patches(patches)
            analysis["model_name"] = model_name
            analysis["injection_type"] = injection_type
            
            all_analyses.append(analysis)
            
            # Print summary
            print(f"  ✅ Valid patches: {analysis['valid_patches']}/{analysis['total_patches']} ({analysis['validity_rate']:.1f}%)")
            print(f"  📝 Total additions: {analysis['total_additions']}")
            print(f"  🗑️  Total deletions: {analysis['total_deletions']}")
            print(f"  📁 Files changed: {analysis['total_files_changed']}")
            
            if analysis['common_issues']:
                print(f"  ⚠️  Common issues:")
                for issue, count in analysis['common_issues'].items():
                    print(f"      {issue}: {count} patches")
    
    # Save detailed analysis
    analysis_file = output_dir / "patch_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(all_analyses, f, indent=2, default=str)
    
    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_models": len(set(a["model_name"] for a in all_analyses)),
        "total_injection_types": len(set(a["injection_type"] for a in all_analyses)),
        "total_patches": sum(a["total_patches"] for a in all_analyses),
        "total_valid_patches": sum(a["valid_patches"] for a in all_analyses),
        "overall_validity_rate": sum(a["valid_patches"] for a in all_analyses) / sum(a["total_patches"] for a in all_analyses) * 100 if sum(a["total_patches"] for a in all_analyses) > 0 else 0,
        "analyses": all_analyses
    }
    
    summary_file = output_dir / "validation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n✅ Analysis completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Detailed analysis: {analysis_file}")
    print(f"Summary: {summary_file}")
    
    print(f"\n📊 Overall Results:")
    print(f"  Total patches: {summary['total_patches']}")
    print(f"  Valid patches: {summary['total_valid_patches']}")
    print(f"  Validity rate: {summary['overall_validity_rate']:.1f}%")

if __name__ == "__main__":
    main()
