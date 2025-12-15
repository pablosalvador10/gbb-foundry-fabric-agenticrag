"""Configuration settings for the Airline Operations Assistant."""

import os

from utils.ml_logging import get_logger

logger = get_logger("app.settings")

try:
    import dotenv

    dotenv.load_dotenv(".env", override=True)
    logger.debug("Loaded .env file")
except ImportError:
    logger.debug("python-dotenv not available, using system env vars")

# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")

# Azure OpenAI
AZURE_OPENAI_API_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")

# UI
PAGE_TITLE = "Airline Operations Assistant"
APP_TITLE = "Airline Operations Assistant"
APP_SUBTITLE = "Powered by Azure AI Foundry + Fabric"
CHAT_CONTAINER_HEIGHT = 500
CHAT_INPUT_PLACEHOLDER = "Ask about flights, weather, operations..."

REQUIRED_VARS = [
    "AZURE_AI_PROJECT_ENDPOINT",
    "AZURE_OPENAI_API_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
]


def validate_configuration() -> bool:
    """Check that required environment variables are set."""
    missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    logger.debug("Configuration validated successfully")
    return True
