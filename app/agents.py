from typing import Optional
import streamlit as st
from agent_framework import ChatAgent
from utils.ml_logging import get_logger

logger = get_logger("app.agents")


def get_fabric_agent(name: str) -> Optional[ChatAgent]:
    """
    Get the initialized Fabric agent from session state.

    This function retrieves the Fabric agent instance from session state
    if it has been properly initialized and is available for use.

    :return: The Fabric agent instance, or None if not available
    :raises: None - function handles missing agent gracefully
    """
    try:
        return st.session_state.get(f"{name}")
    except Exception as e:
        logger.error(f"Error retrieving Fabric agent: {str(e)}")
        return None


def is_fabric_agent_available(name: str) -> bool:
    """
    Check if the Fabric agent is properly initialized and available.

    This function verifies the availability of the Fabric agent
    in session state to ensure it can be used for processing requests.

    :return: True if the agent is available, False otherwise
    :raises: None - function handles errors gracefully
    """
    try:
        return st.session_state.get(f"{name}") is not None
    except Exception as e:
        logger.error(f"Error checking Fabric agent availability: {str(e)}")
        return False


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
