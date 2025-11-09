import streamlit as st
from utils.ml_logging import get_logger
from app.agents import setup_fabric_clients, setup_unified_fabric_agent
from azure.identity import InteractiveBrowserCredential

logger = get_logger("app.services")


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


def initialize_fabric_services() -> None:
    """
    Initialize all Fabric-related services in the correct order.

    This function orchestrates the initialization of all Fabric components
    and should be called during application startup to ensure proper configuration.

    :return: None
    :raises: Exception if any service initialization fails
    """
    try:
        logger.info("Initializing Fabric services")
        setup_fabric_credentials()
        setup_fabric_clients()
        setup_unified_fabric_agent()
        logger.info("Fabric services initialization completed successfully")
    except Exception as e:
        logger.error(f"Fabric services initialization failed: {str(e)}")
        raise


def setup_fabric_credentials() -> None:
    """
    Initialize Fabric authentication credentials.

    This function sets up Interactive Browser Credential for authenticating
    with Microsoft Fabric services and stores it in session state.

    :return: None
    :raises: Exception if credential initialization fails
    """
    if "cred" not in st.session_state:
        try:
            st.session_state.cred = InteractiveBrowserCredential()
            logger.info("Fabric credentials initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Fabric credentials: {str(e)}")
            st.session_state.cred = None
            raise
