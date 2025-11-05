"""
Azure client configuration and initialization utilities.
"""

import os
from typing import Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Try to import Azure AI Foundry components (optional)
try:
    from azure.ai.projects import AIProjectClient
    from azure.core.credentials import AzureKeyCredential
    AI_FOUNDRY_AVAILABLE = True
except ImportError:
    AI_FOUNDRY_AVAILABLE = False
    AIProjectClient = None
    AzureKeyCredential = None

# Load environment variables
load_dotenv()

class AzureClientManager:
    """Manages Azure service clients with proper authentication and configuration."""
    
    def __init__(self):
        self.openai_client = None
        self.ai_foundry_client = None
        # Don't validate immediately - validate when clients are requested
    
    def _validate_environment(self):
        """Validate required environment variables are set."""
        required_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_DEPLOYMENT_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def get_openai_client(self) -> AzureOpenAI:
        """Get configured Azure OpenAI client."""
        if self.openai_client is None:
            # Validate OpenAI environment when client is requested
            self._validate_environment()
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        return self.openai_client
    
    def get_model_config(self, model_name: Optional[str] = None) -> dict:
        """Get model configuration for evaluations."""
        return {
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            "azure_deployment": model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        }
    
    def get_ai_foundry_client(self):
        """Get Azure AI Foundry project client if available and configured."""
        if not AI_FOUNDRY_AVAILABLE:
            return None
            
        if self.ai_foundry_client is None:
            # Check if AI Foundry environment variables are set
            endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
            api_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY")
            project_name = os.getenv("AZURE_AI_FOUNDRY_PROJECT_NAME")
            
            if endpoint and api_key and project_name:
                try:
                    # Use API key authentication
                    credential = AzureKeyCredential(api_key)
                    self.ai_foundry_client = AIProjectClient(
                        endpoint=endpoint,
                        credential=credential,
                        project_name=project_name
                    )
                except Exception as e:
                    print(f"⚠️ Failed to initialize AI Foundry client: {e}")
                    return None
            elif endpoint and project_name:
                # Fallback to DefaultAzureCredential (for managed identity/CLI auth)
                try:
                    credential = DefaultAzureCredential()
                    self.ai_foundry_client = AIProjectClient(
                        endpoint=endpoint,
                        credential=credential,
                        project_name=project_name
                    )
                except Exception as e:
                    print(f"⚠️ Failed to initialize AI Foundry client with DefaultAzureCredential: {e}")
                    return None
        
        return self.ai_foundry_client
    
    def is_ai_foundry_enabled(self) -> bool:
        """Check if Azure AI Foundry integration is available and configured."""
        return (AI_FOUNDRY_AVAILABLE and 
                os.getenv("AZURE_AI_FOUNDRY_PROJECT_NAME") and 
                os.getenv("AZURE_AI_FOUNDRY_ENDPOINT"))

# Singleton instance for easy access
azure_manager = AzureClientManager()