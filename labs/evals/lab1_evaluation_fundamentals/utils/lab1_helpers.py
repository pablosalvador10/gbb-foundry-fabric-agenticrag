"""
Helper functions specific to Lab 1: Evaluation Fundamentals
"""

import json
import time
from typing import List, Dict, Any
from openai import AzureOpenAI

def demonstrate_llm_variability(client: AzureOpenAI, 
                              deployment_name: str, 
                              prompt: str, 
                              num_runs: int = 3) -> List[str]:
    """
    Demonstrate the non-deterministic nature of LLM outputs by running the same prompt multiple times.
    """
    responses = []
    
    print(f"Running the same prompt {num_runs} times to show variability...")
    print(f"Prompt: {prompt}")
    print("-" * 80)
    
    for i in range(num_runs):
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7  # Higher temperature for more variability
            )
            
            content = response.choices[0].message.content.strip()
            responses.append(content)
            
            print(f"Run {i+1}:")
            print(content)
            print("-" * 80)
            
            # Add small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in run {i+1}: {e}")
            responses.append(f"Error: {e}")
    
    return responses

def create_evaluation_dataset_from_responses(original_prompt: str, 
                                           responses: List[str], 
                                           context: str = "") -> List[Dict[str, Any]]:
    """
    Create an evaluation dataset from multiple responses to the same prompt.
    """
    dataset = []
    
    for i, response in enumerate(responses):
        entry = {
            "query": original_prompt,
            "response": response,
            "context": context,
            "run_id": i + 1
        }
        dataset.append(entry)
    
    return dataset

def print_evaluation_insights(results: Dict[str, Any]) -> None:
    """
    Print insights about evaluation results in a beginner-friendly way.
    """
    print("🔍 EVALUATION INSIGHTS")
    print("=" * 50)
    
    if 'metrics' in results:
        metrics = results['metrics']
        
        print("📊 Overall Metrics:")
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"  • {metric_name}: {value:.3f}")
                
                # Provide interpretation
                if 'relevance' in metric_name.lower():
                    interpretation = get_relevance_interpretation(value)
                elif 'coherence' in metric_name.lower():
                    interpretation = get_coherence_interpretation(value)
                elif 'fluency' in metric_name.lower():
                    interpretation = get_fluency_interpretation(value)
                elif 'groundedness' in metric_name.lower():
                    interpretation = get_groundedness_interpretation(value)
                else:
                    interpretation = "Higher values generally indicate better performance"
                
                print(f"    → {interpretation}")
    
    if 'rows' in results and len(results['rows']) > 0:
        print(f"\n📈 Individual Results (showing first 3 of {len(results['rows'])}):")
        for i, row in enumerate(results['rows'][:3]):
            print(f"\n  Result {i+1}:")
            if 'outputs' in row:
                for metric, value in row['outputs'].items():
                    if isinstance(value, (int, float)):
                        print(f"    • {metric}: {value:.3f}")

def get_relevance_interpretation(score: float) -> str:
    """Provide human-readable interpretation of relevance scores."""
    if score >= 4.0:
        return "Excellent - Response directly addresses the question"
    elif score >= 3.0:
        return "Good - Response is mostly relevant with minor issues"
    elif score >= 2.0:
        return "Fair - Response has some relevance but may be incomplete"
    else:
        return "Poor - Response doesn't adequately address the question"

def get_coherence_interpretation(score: float) -> str:
    """Provide human-readable interpretation of coherence scores."""
    if score >= 4.0:
        return "Excellent - Response is very clear and well-structured"
    elif score >= 3.0:
        return "Good - Response is mostly coherent with good flow"
    elif score >= 2.0:
        return "Fair - Response is somewhat coherent but may have issues"
    else:
        return "Poor - Response lacks clear structure or logical flow"

def get_fluency_interpretation(score: float) -> str:
    """Provide human-readable interpretation of fluency scores."""
    if score >= 4.0:
        return "Excellent - Response is very natural and well-written"
    elif score >= 3.0:
        return "Good - Response flows well with minor language issues"
    elif score >= 2.0:
        return "Fair - Response is understandable but may have language issues"
    else:
        return "Poor - Response has significant language or grammar problems"

def get_groundedness_interpretation(score: float) -> str:
    """Provide human-readable interpretation of groundedness scores."""
    if score >= 4.0:
        return "Excellent - Response is fully supported by the provided context"
    elif score >= 3.0:
        return "Good - Response is mostly grounded in the context"
    elif score >= 2.0:
        return "Fair - Response partially uses the context but may add unsupported claims"
    else:
        return "Poor - Response contains claims not supported by the context"

def save_lab1_results(results: Dict[str, Any], filename: str = "evaluation_results.json") -> None:
    """Save Lab 1 results with timestamp and metadata."""
    import os
    from datetime import datetime
    
    # Add metadata
    results['lab'] = 'Lab 1: Evaluation Fundamentals'
    results['timestamp'] = datetime.now().isoformat()
    results['total_evaluations'] = len(results.get('rows', []))
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Save results
    output_path = os.path.join(data_dir, filename)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Results saved to: {output_path}")

# Sample prompts that work well for demonstrating evaluation concepts
DEMO_PROMPTS = {
    "factual": "What is the capital of Japan and what is it known for?",
    "explanatory": "Explain how vaccines work to prevent diseases.",
    "creative": "Write a short story about a robot learning to paint.",
    "analytical": "Compare the advantages and disadvantages of renewable energy sources.",
    "instruction": "Provide step-by-step instructions for making a paper airplane."
}