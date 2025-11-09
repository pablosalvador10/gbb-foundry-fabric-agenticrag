import os
from typing import Annotated
from pydantic import Field
from utils.ml_logging import get_logger
from src.agents.azure_openai.main import setup_aoai_agent
from src.agents.dataagents.main import ask_fabric_agent
from agent_registry.config_loader import load_agent_config

logger = get_logger("agent_registry.azure_openai.airline_ops_context_agent")

# Global credential cache - will be set by main app
_azure_credential = None

def set_azure_credential(credential):
    """Set the cached Azure credential for this module."""
    global _azure_credential
    _azure_credential = credential
    logger.info("🔐 Azure credential cached for AirlineOpsContext agent")

# ===============================
# LOAD DYNAMIC CONFIGURATION
# ===============================

# Load configuration from YAML file (location specified in .env)
# Environment variable: AIRLINE_OPS_CONTEXT_CONFIG
config = load_agent_config("AIRLINE_OPS_CONTEXT")

# ===============================
# EXTRACT CONFIGURATION VALUES
# ===============================

NAME = config["name"]
DESCRIPTION = config["description"]
INSTRUCTIONS = config["instructions"]
ENDPOINT = config["azure_openai"]["endpoint"]
API_KEY = config["azure_openai"]["api_key"]
DEPLOYMENT_NAME = config["azure_openai"]["deployment"]
AIRPORT_INFO_ENDPOINT = config["fabric_endpoints"]["airport_info"]

logger.info(f"Loaded configuration for agent: {NAME}")

# ===============================
# TOOLS
# ===============================


def retrieve_operational_context(
    query: Annotated[
        str,
        Field(
            description="Operational query about flights, baggage, routes, airports, or SLAs"
        ),
    ]
) -> str:
    """
    Retrieve trusted operational context from Microsoft Fabric data sources.

    This tool queries the governed Fabric data agent to retrieve accurate
    operational information about airline operations including flights,
    baggage handling, routes, airport operations, and SLA metrics.

    :param query: The operational question or data request
    :return: Retrieved operational context and data from Fabric
    """
    try:
        logger.info("=" * 80)
        logger.info("🔧 TOOL EXECUTION: retrieve_operational_context")
        logger.info(f"📋 Query: {query}")
        logger.info("=" * 80)

        # Query the Fabric agent with the airport info endpoint
        # Use cached credential if available
        response = ask_fabric_agent(
            endpoint=AIRPORT_INFO_ENDPOINT, 
            question=query,
            credential=_azure_credential
        )

        logger.info("✅ Operational context retrieved successfully from Fabric")
        logger.info("=" * 80)
        return response

    except Exception as e:
        error_msg = f"Error retrieving operational context: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.info("=" * 80)
        return error_msg


# ===============================
# AGENT SETUP
# ===============================

airline_ops_context_agent = setup_aoai_agent(
    name=NAME,
    endpoint=ENDPOINT,
    api_key=API_KEY,
    deployment_name=DEPLOYMENT_NAME,
    tools=[retrieve_operational_context],
    instructions=INSTRUCTIONS,
    description=DESCRIPTION,
)
