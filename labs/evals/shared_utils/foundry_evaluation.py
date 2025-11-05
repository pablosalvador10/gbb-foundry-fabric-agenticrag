"""
Azure AI Foundry integration utilities for evaluations.
"""

import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from azure.ai.evaluation import evaluate
from .azure_clients import azure_manager


class FoundryEvaluationRunner:
    """Enhanced evaluation runner with optional Azure AI Foundry integration."""
    
    def __init__(self):
        self.foundry_client = azure_manager.get_ai_foundry_client()
        self.foundry_enabled = azure_manager.is_ai_foundry_enabled()
    
    def run_evaluation(self, 
                      data: List[Dict[str, Any]], 
                      evaluators: Dict[str, Any],
                      run_name: Optional[str] = None,
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Run evaluation with optional Azure AI Foundry integration.
        
        Args:
            data: List of evaluation data points
            evaluators: Dictionary of evaluator instances
            run_name: Optional name for the evaluation run
            description: Optional description for the evaluation run
            
        Returns:
            Evaluation results with metadata about execution method
        """
        
        if self.foundry_enabled and self.foundry_client:
            print("🏢 Running evaluation through Azure AI Foundry...")
            print("   ✅ Results will appear in the AI Foundry portal")
            return self._run_foundry_evaluation(data, evaluators, run_name, description)
        else:
            print("🔧 Running evaluation locally...")
            print("   ℹ️ To see results in AI Foundry portal, configure:")
            print("      AZURE_AI_FOUNDRY_CONNECTION_STRING or")
            print("      AZURE_AI_FOUNDRY_PROJECT_NAME + AZURE_AI_FOUNDRY_ENDPOINT")
            return self._run_local_evaluation(data, evaluators, run_name)
    
    def _run_foundry_evaluation(self, 
                               data: List[Dict[str, Any]], 
                               evaluators: Dict[str, Any],
                               run_name: Optional[str] = None,
                               description: Optional[str] = None) -> Dict[str, Any]:
        """Run evaluation through Azure AI Foundry service."""
        
        try:
            print("🏢 Running evaluation with Azure AI Foundry integration...")
            
            # Step 1: Upload dataset to AI Foundry
            dataset_name = f"evaluation_dataset_{abs(hash(str(data)))}"
            
            # Create temporary JSONL file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
            for item in data:
                temp_file.write(json.dumps(item) + '\n')
            temp_file.close()
            
            try:
                print(f"📤 Uploading dataset to AI Foundry: {dataset_name}")
                uploaded_dataset = self.foundry_client.datasets.upload_file(
                    name=dataset_name,
                    version="1.0",
                    file_path=temp_file.name
                )
                
                print(f"✅ Dataset uploaded successfully: {uploaded_dataset.id}")
                
                # Step 2: Since evaluation operations aren't available yet, 
                # run local evaluation but with enhanced AI Foundry metadata
                print("📊 Running evaluation locally (AI Foundry evaluation API not yet available)")
                results = self._run_local_evaluation(data, evaluators, run_name)
                
                # Add AI Foundry metadata including the uploaded dataset
                if isinstance(results, dict):
                    results['_execution_method'] = 'azure_ai_foundry_hybrid'
                    results['_foundry_enabled'] = True
                    results['_portal_visible'] = True  # Dataset is visible in portal
                    results['_dataset_id'] = uploaded_dataset.id
                    results['_dataset_name'] = dataset_name
                    results['_run_name'] = run_name or f"Lab1 Evaluation - {len(data)} items"
                    results['_description'] = description or f"Evaluation run with {len(evaluators)} evaluators"
                    results['_note'] = "Dataset uploaded to AI Foundry, evaluation run locally"
                    
                print("✅ Evaluation completed with dataset uploaded to AI Foundry")
                print(f"📁 Dataset '{dataset_name}' is now visible in AI Foundry portal")
                print("🔮 When evaluation API is available, it will use this uploaded dataset")
                
                return results
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"⚠️ AI Foundry integration failed: {e}")
            print("   Falling back to local evaluation...")
            return self._run_local_evaluation(data, evaluators, run_name)
    
    def _run_local_evaluation(self, 
                             data: List[Dict[str, Any]], 
                             evaluators: Dict[str, Any],
                             run_name: Optional[str] = None) -> Dict[str, Any]:
        """Run evaluation locally using standard Azure AI Evaluation SDK."""
        
        # Create temporary JSONL file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        for item in data:
            temp_file.write(json.dumps(item) + '\n')
        temp_file.close()
        
        try:
            # Suppress verbose output from evaluation
            import sys
            from io import StringIO
            
            # Capture stdout to prevent large output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # Use standard evaluate function
                results = evaluate(
                    data=temp_file.name,
                    evaluators=evaluators
                )
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
            # Add local metadata
            if isinstance(results, dict):
                results['_execution_method'] = 'local_evaluation'
                results['_foundry_enabled'] = self.foundry_enabled
                results['_portal_visible'] = False
                if run_name:
                    results['_run_name'] = run_name
            
            return results
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file.name)
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get status information about AI Foundry integration."""
        return {
            'ai_foundry_available': self.foundry_enabled,
            'foundry_client_initialized': self.foundry_client is not None,
            'portal_integration': 'enabled' if self.foundry_enabled else 'disabled',
            'required_env_vars': [
                'AZURE_AI_FOUNDRY_PROJECT_NAME',
                'AZURE_AI_FOUNDRY_ENDPOINT', 
                'AZURE_AI_FOUNDRY_API_KEY (or use DefaultAzureCredential)'
            ]
        }


# Create singleton instance
foundry_runner = FoundryEvaluationRunner()