"""
Common evaluation utilities and helper functions.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

def load_evaluation_data(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation data from JSONL or JSON file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Evaluation data file not found: {file_path}")
    
    data = []
    if file_path.suffix == '.jsonl':
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line.strip()))
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    return data

def save_evaluation_results(results: Dict[str, Any], output_path: str) -> None:
    """Save evaluation results to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def format_evaluation_summary(results: Dict[str, Any]) -> str:
    """Format evaluation results into a readable summary."""
    summary = ["=" * 60, "EVALUATION SUMMARY", "=" * 60]
    
    if 'metrics' in results:
        summary.append("\nOverall Metrics:")
        for metric, value in results['metrics'].items():
            if isinstance(value, float):
                summary.append(f"  {metric}: {value:.3f}")
            else:
                summary.append(f"  {metric}: {value}")
    
    if 'rows' in results:
        summary.append(f"\nTotal Evaluations: {len(results['rows'])}")
    
    return "\n".join(summary)

def create_comparison_dataframe(results_dict: Dict[str, Dict]) -> pd.DataFrame:
    """Create a comparison DataFrame from multiple evaluation results."""
    comparison_data = []
    
    for model_name, results in results_dict.items():
        if 'metrics' in results:
            row = {'model': model_name}
            row.update(results['metrics'])
            comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)

def calculate_cost_metrics(results: Dict[str, Any], cost_per_1k_tokens: float = 0.002) -> Dict[str, float]:
    """Calculate cost metrics from evaluation results."""
    if 'rows' not in results:
        return {}
    
    total_tokens = 0
    for row in results['rows']:
        if 'outputs' in row and 'token_count' in row['outputs']:
            total_tokens += row['outputs']['token_count']
    
    total_cost = (total_tokens / 1000) * cost_per_1k_tokens
    avg_cost_per_eval = total_cost / len(results['rows']) if results['rows'] else 0
    
    return {
        'total_tokens': total_tokens,
        'total_cost_usd': total_cost,
        'avg_cost_per_evaluation': avg_cost_per_eval,
        'cost_per_1k_tokens': cost_per_1k_tokens
    }