"""
Configuration and Environment Settings for Multi-Agent Streamlit Application.

This module centralizes all environment variables, constants, and configuration parameters
for the enterprise multi-agent system.
"""

import os
from typing import Dict, List
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

# ---- FABRIC AGENT ENDPOINTS ----
FABRIC_ENDPOINTS: Dict[str, str] = {
    "product_discovery": "https://msitapi.fabric.microsoft.com/v1/workspaces/409e30ce-b2ad-4c80-a54d-d645227322e4/aiskills/672fba68-a7d0-4c85-99e9-9ed6fe8ef1d1/aiassistant/openai",
    "sales_data": "https://msitapi.fabric.microsoft.com/v1/workspaces/409e30ce-b2ad-4c80-a54d-d645227322e4/aiskills/360ef9b6-c087-4e72-ab7c-f157007cda3a/aiassistant/openai",
    "airport_info": "https://msitapi.fabric.microsoft.com/v1/workspaces/00ae18cb-e789-4d42-be8d-a5b47e524e22/aiskills/1d266d5d-cbbb-4099-9ef2-69fa875e4f89/aiassistant/openai",
}

# ---- AUTHENTICATION SCOPES ----
FABRIC_SCOPE: str = "https://api.fabric.microsoft.com/.default"

# ---- AZURE AI PROJECT CONFIGURATION ----
AZURE_AI_PROJECT_ENDPOINT: str = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")

# ---- AZURE OPENAI CONFIGURATION ----
AZURE_OPENAI_API_ENDPOINT: str = os.getenv("AZURE_OPENAI_API_ENDPOINT", "")
AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID: str = os.getenv(
    "AZURE_AOAI_CHAT_MODEL_NAME_DEPLOYMENT_ID", ""
)

# ---- AGENT IDS ----
FOUNDRY_AGENT_ID: str = "asst_qLI4yveCYhur62Ya4QhEkvFz"

# ---- FABRIC API CONFIGURATION ----
FABRIC_API_VERSION: str = "2024-05-01-preview"

# ---- TIMEOUT SETTINGS ----
DEFAULT_POLL_INTERVAL_SEC: int = 2
DEFAULT_TIMEOUT_SEC: int = 300

# ---- AGENT ROUTING KEYWORDS ----
FABRIC_KEYWORDS = [
    "sales",
    "revenue",
    "product",
    "mard",
    "glucose",
    "airport",
    "airports",
    "analytics",
    "metrics",
    "kpi",
    "airline",
    "airlines",
    "airplane",
    "airplanes",
    "aircraft",
    "flight",
    "flights",
    "route",
    "routes",
    "delay",
    "delays",
    "departure",
    "arrival",
    "terminal",
    "gate",
    "gates",
    "runway",
    "runways",
    "aviation",
    "crew",
    "baggage",
    "booking",
    "bookings",
    "ground service",
    "screening",
    "components",
    "legs",
    "training",
    "conditions",
]

FOUNDRY_KEYWORDS = [
    "etd",
    "electronic trade documents",
    "customs",
    "commercial invoice",
    "trade documents",
    "ship manager",
    "letterhead",
    "signature",
    "proforma invoice",
    "certificate of origin",
    "nafta",
    "clearance",
    "broker",
    "upload",
    "document upload",
    "invoice upload",
]

COPILOT_KEYWORDS = [
    "rate",
    "rates",
    "pricing",
    "cost",
    "price",
    "zone",
    "weight",
    "dimensional",
    "chargeable",
    "service",
    "express",
    "ground",
    "delivery",
    "terms",
    "surcharge",
    "fee",
    "fuel",
    "residential",
    "one rate",
    "freight",
    "sameday",
    "fedex ground",
    "fedex express",
    "package",
    "pound",
    "shipping cost",
]

# ---- AGENT DESCRIPTIONS ----
FEDEX_RATES_AGENT_DESCRIPTION: str = (
    "You are a specialized AI assistant with expertise in FedEx shipping rates, "
    "pricing calculations, terms and conditions, and service options. Your primary "
    "function is to help customers understand and navigate FedEx's complex pricing "
    "structure, calculate shipping costs, interpret service terms, and select "
    "appropriate shipping solutions based on their needs. Guide customers through "
    "step-by-step rate calculation processes, explain weight calculations, help "
    "identify zones, clarify pricing options, explain service differences, interpret "
    "terms and conditions, and identify applicable fees and surcharges. Always "
    "direct customers to official FedEx tools (fedex.com/ratetools) for real-time "
    "quotes and emphasize that you work with standard published rates effective "
    "January 6, 2025."
)

FEDEX_ETD_AGENT_INSTRUCTIONS: str = (
    "You are a FedEx Electronic Trade Documents expert. Help users with ETD setup, "
    "configuration, document requirements, troubleshooting, and best practices for "
    "international shipping."
)

UNIFIED_FABRIC_AGENT_INSTRUCTIONS: str = (
    "You are a helpful assistant with access to specialized data sources. "
    "If the user asks about PRODUCT discovery (catalogs, reviews, inventory, shopping, etc.), "
    "call the `product_discovery_qna` tool. "
    "If the user asks about SALES analytics (ARR, pipeline, bookings, forecast, revenue, etc.), "
    "call the `sales_data_qna` tool. "
    "If the user asks about AIRPORT information (terminals, services, amenities, operations), "
    "call the `airport_info_qna` tool. "
    "You can use multiple tools if the question spans multiple domains. "
    "Otherwise, answer directly using your general knowledge."
)

# ---- UI CONFIGURATION ----
PAGE_TITLE: str = "R+D Intelligent Multi-Agent Assistant"
APP_TITLE: str = "Research Intelligent Assistant"
APP_SUBTITLE: str = "powered by Azure AI + Fabric"
CHAT_CONTAINER_HEIGHT: int = 500
CHAT_INPUT_PLACEHOLDER: str = "What do you want to know about..."


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
        "AZURE_OPENAI_KEY",
        "AZURE_AOAI_CHAT_MODEL_NAME_DEPLOYMENT_ID",
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
