"""
Dataset manipulation and generation utilities.
"""

import json
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

def create_qa_dataset(questions_answers: List[tuple], 
                     contexts: Optional[List[str]] = None,
                     save_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Create a Q&A evaluation dataset from questions and answers."""
    dataset = []
    
    for i, (question, answer) in enumerate(questions_answers):
        entry = {
            "question": question,
            "answer": answer,
            "ground_truth": answer  # For evaluation purposes
        }
        
        if contexts and i < len(contexts):
            entry["context"] = contexts[i]
        
        dataset.append(entry)
    
    if save_path:
        save_dataset(dataset, save_path)
    
    return dataset

def save_dataset(dataset: List[Dict[str, Any]], file_path: str, format: str = "jsonl") -> None:
    """Save dataset to file in specified format."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format.lower() == "jsonl":
        with open(file_path, 'w', encoding='utf-8') as f:
            for entry in dataset:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

def sample_dataset(dataset: List[Dict[str, Any]], 
                  sample_size: int, 
                  random_seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Sample a subset of the dataset."""
    if random_seed:
        random.seed(random_seed)
    
    if sample_size >= len(dataset):
        return dataset.copy()
    
    return random.sample(dataset, sample_size)

def validate_dataset_schema(dataset: List[Dict[str, Any]], 
                          required_fields: List[str]) -> List[str]:
    """Validate that dataset entries contain required fields."""
    errors = []
    
    for i, entry in enumerate(dataset):
        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            errors.append(f"Entry {i}: Missing fields {missing_fields}")
    
    return errors

def merge_datasets(*datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge multiple datasets into one."""
    merged = []
    for dataset in datasets:
        merged.extend(dataset)
    return merged

def filter_dataset(dataset: List[Dict[str, Any]], 
                  filter_fn: callable) -> List[Dict[str, Any]]:
    """Filter dataset based on a custom function."""
    return [entry for entry in dataset if filter_fn(entry)]

# Common sample datasets for quick testing
SAMPLE_QA_PAIRS = [
    ("What is the capital of France?", "The capital of France is Paris."),
    ("How do you calculate the area of a circle?", "The area of a circle is calculated using the formula πr², where r is the radius."),
    ("What is machine learning?", "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed."),
    ("Who wrote Romeo and Juliet?", "Romeo and Juliet was written by William Shakespeare."),
    ("What is the speed of light?", "The speed of light in a vacuum is approximately 299,792,458 meters per second.")
]

def create_sample_dataset(size: int = 5, save_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Create a sample Q&A dataset for testing."""
    sample_pairs = SAMPLE_QA_PAIRS[:size] if size <= len(SAMPLE_QA_PAIRS) else SAMPLE_QA_PAIRS
    return create_qa_dataset(sample_pairs, save_path=save_path)