"""
Configuration and Environment Settings for Airline Operations Assistant.

This module centralizes all environment variables, constants, and configuration parameters
for the Airline Intelligent Assistant multi-agent system.
"""

import os
from typing import List
from utils.ml_logging import get_logger

logger = get_logger("app.settings")

try:
    import dotenv

    dotenv.load_dotenv(".env", override=True)
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning(
        "python-dotenv not available, using system environment variables only"
    )

# ---- AZURE AI PROJECT CONFIGURATION ----
AZURE_AI_PROJECT_ENDPOINT: str = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")

# ---- AZURE OPENAI CONFIGURATION ----
AZURE_OPENAI_API_ENDPOINT: str = os.getenv("AZURE_OPENAI_API_ENDPOINT", "")
AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")

# ---- UI CONFIGURATION ----
PAGE_TITLE: str = "Airline Operations Assistant"
APP_TITLE: str = "Airline Operations Decision Assistant"
APP_SUBTITLE: str = "Powered by Azure AI Multi-Agent Framework"
CHAT_CONTAINER_HEIGHT: int = 500
CHAT_INPUT_PLACEHOLDER: str = "Ask about flights, weather, operations, or real-time data..."


def validate_configuration() -> bool:
    """
    Validate that all required environment variables are set.

    This function checks for the presence of all critical environment variables
    required for the multi-agent system to function properly.

    :return: True if all required variables are present, False otherwise
    :raises: None - function handles missing variables gracefully
    """
    required_vars: List[str] = [
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_OPENAI_API_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ]

    try:
        missing_vars: List[str] = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            return False

        logger.info("All required environment variables validated successfully")
        return True

    except Exception as e:
        logger.error(f"Error during configuration validation: {str(e)}")
        return False

