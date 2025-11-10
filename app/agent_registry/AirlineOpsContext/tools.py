import os
from typing import Annotated
from pydantic import Field
from src.agents.dataagents.main import ask_fabric_agent
from utils.ml_logging import get_logger

logger = get_logger("src.agents.dataagents")
AIRPORT_INFO_ENDPOINT = os.getenv("AIRPORT_INFO_ENDPOINT")
_azure_credential = None

def set_azure_credential(credential):
    """Set the cached Azure credential for this module."""
    global _azure_credential
    _azure_credential = credential
    logger.info("🔐 Azure credential cached for AirlineOpsContext tools")


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