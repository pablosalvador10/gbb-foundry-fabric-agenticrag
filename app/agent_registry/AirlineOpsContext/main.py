from app.agent_registry.AirlineOpsContext import tools as ops_tools
from app.agent_registry.AirlineOpsContext.tools import retrieve_operational_context
from app.agent_registry.config_loader import load_agent_config
from src.agents.azure_openai.main import setup_aoai_agent
from utils.ml_logging import get_logger

logger = get_logger("agent_registry.azure_openai.airline_ops_context_agent")

# ===============================
# CREDENTIAL CACHING
# ===============================

# Global variable to cache Azure credential (set from main app)
_azure_credential = None


def set_azure_credential(credential):
    """
    Set the cached Azure credential to be used by this agent.

    This allows the main app to pass a pre-authenticated credential
    to avoid repeated authentication prompts.

    Args:
        credential: Azure credential object (e.g., InteractiveBrowserCredential)
    """
    global _azure_credential
    _azure_credential = credential
    ops_tools.set_azure_credential(credential)
    ops_tools.set_airport_endpoint(AIRPORT_INFO_ENDPOINT)
    logger.info("Azure credential set for AirlineOpsContext agent and tools")


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
