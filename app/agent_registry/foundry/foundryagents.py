"""
Foundry Agent Management Module
Handles Azure AI Foundry agents and project client setup.
"""

import streamlit as st
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.settings import AZURE_AI_PROJECT_ENDPOINT, FOUNDRY_AGENT_ID, FEDEX_ETD_AGENT_INSTRUCTIONS
from utils.ml_logging import get_logger

logger = get_logger()


def setup_foundry_project_client() -> None:
    """
    Initialize Azure AI Project client for Foundry services.
    
    Sets up the foundry_project in session state for later use by Foundry agents.
    """
    if 'foundry_project' not in st.session_state:
        try:
            st.session_state.foundry_project = AIProjectClient(
                endpoint=AZURE_AI_PROJECT_ENDPOINT, 
                credential=AzureCliCredential()
            )
            logger.info("✅ Initialized Foundry project client")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Foundry project: {e}")
            st.session_state.foundry_project = None


def setup_foundry_agent() -> None:
    """
    Initialize the FedEx ETD Foundry agent.
    
    Creates a ChatAgent configured to work with Azure AI Foundry services
    for FedEx Electronic Trade Documents expertise.
    """
    if "foundry_agent" not in st.session_state:
        if st.session_state.foundry_project is None:
            logger.warning("❌ Foundry project not available, skipping Foundry agent")
            st.session_state.foundry_agent = None
        else:
            try:
                chat_client = AzureAIAgentClient(
                    project_client=st.session_state.foundry_project, 
                    agent_id=FOUNDRY_AGENT_ID
                )
                
                st.session_state.foundry_agent = ChatAgent(
                    chat_client=chat_client,
                    name="FedExETDAgent", 
                    description="FedEx Electronic Trade Documents specialist with expertise in international shipping documentation.",
                    instructions=FEDEX_ETD_AGENT_INSTRUCTIONS
                )
                logger.info("✅ Created FedEx ETD Foundry agent")
            except Exception as e:
                logger.error(f"❌ Failed to create Foundry agent: {e}")
                st.session_state.foundry_agent = None


def initialize_foundry_services() -> None:
    """
    Initialize all Foundry-related services in the correct order.
    
    This function should be called during application startup to ensure
    all Foundry components are properly configured.
    """
    logger.info("🔧 Initializing Foundry services...")
    setup_foundry_project_client()
    setup_foundry_agent()
    logger.info("✅ Foundry services initialization complete")


def get_foundry_agent() -> ChatAgent:
    """
    Get the initialized Foundry agent from session state.
    
    Returns:
        ChatAgent: The FedEx ETD Foundry agent, or None if not available
    """
    return st.session_state.get('foundry_agent')


def is_foundry_agent_available() -> bool:
    """
    Check if the Foundry agent is properly initialized and available.
    
    Returns:
        bool: True if the agent is available, False otherwise
    """
    return st.session_state.get('foundry_agent') is not None