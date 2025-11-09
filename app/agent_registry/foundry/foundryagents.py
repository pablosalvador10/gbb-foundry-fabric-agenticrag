"""
Foundry Agent Management Module.

This module handles Azure AI Foundry agents and project client setup
for the enterprise multi-agent system.
"""

import streamlit as st
from typing import Optional
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.settings import (
    AZURE_AI_PROJECT_ENDPOINT,
    FOUNDRY_AGENT_ID,
    FEDEX_ETD_AGENT_INSTRUCTIONS,
)
from utils.ml_logging import get_logger

logger = get_logger("agent_registry.foundry.foundryagents")


def setup_foundry_project_client() -> None:
    """
    Initialize Azure AI Project client for Foundry services.

    This function sets up the foundry_project in session state for later use
    by Foundry agents, enabling connection to Azure AI Foundry services.

    :return: None
    :raises: Exception if client initialization fails
    """
    if "foundry_project" not in st.session_state:
        try:
            st.session_state.foundry_project = AIProjectClient(
                endpoint=AZURE_AI_PROJECT_ENDPOINT, credential=AzureCliCredential()
            )
            logger.info("Foundry project client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Foundry project client: {str(e)}")
            st.session_state.foundry_project = None
            raise


def setup_foundry_agent() -> None:
    """
    Initialize the FedEx ETD Foundry agent.

    This function creates a ChatAgent configured to work with Azure AI Foundry services
    for FedEx Electronic Trade Documents expertise and stores it in session state.

    :return: None
    :raises: Exception if agent creation fails
    """
    if "foundry_agent" not in st.session_state:
        if st.session_state.foundry_project is None:
            logger.warning("Foundry project not available, skipping Foundry agent")
            st.session_state.foundry_agent = None
        else:
            try:
                chat_client = AzureAIAgentClient(
                    project_client=st.session_state.foundry_project,
                    agent_id=FOUNDRY_AGENT_ID,
                )

                st.session_state.foundry_agent = ChatAgent(
                    chat_client=chat_client,
                    name="FedExETDAgent",
                    description="FedEx Electronic Trade Documents specialist with expertise in international shipping documentation.",
                    instructions=FEDEX_ETD_AGENT_INSTRUCTIONS,
                )
                logger.info("FedEx ETD Foundry agent created successfully")
            except Exception as e:
                logger.error(f"Failed to create Foundry agent: {str(e)}")
                st.session_state.foundry_agent = None
                raise


def initialize_foundry_services() -> None:
    """
    Initialize all Foundry-related services in the correct order.

    This function orchestrates the initialization of all Foundry components
    and should be called during application startup to ensure proper configuration.

    :return: None
    :raises: Exception if any service initialization fails
    """
    try:
        logger.info("Initializing Foundry services")
        setup_foundry_project_client()
        setup_foundry_agent()
        logger.info("Foundry services initialization completed successfully")
    except Exception as e:
        logger.error(f"Foundry services initialization failed: {str(e)}")
        raise
def get_foundry_agent() -> Optional[ChatAgent]:
    """
    Get the initialized Foundry agent from session state.

    This function retrieves the FedEx ETD Foundry agent instance from the
    Streamlit session state if available.

    :return: The FedEx ETD Foundry agent instance, or None if not available
    :raises: None - function handles missing agent gracefully
    """
    try:
        return st.session_state.get("foundry_agent")
    except Exception as e:
        logger.error(f"Error retrieving Foundry agent: {str(e)}")
        return None


def is_foundry_agent_available() -> bool:
    """
    Check if the Foundry agent is properly initialized and available.

    This function verifies the availability of the Foundry agent in session state
    to ensure it can be used for processing requests.

    :return: True if the agent is available, False otherwise
    :raises: None - function handles errors gracefully
    """
    try:
        return st.session_state.get("foundry_agent") is not None
    except Exception as e:
        logger.error(f"Error checking Foundry agent availability: {str(e)}")
        return False
