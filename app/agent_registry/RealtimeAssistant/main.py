"""
Realtime Assistant Agent Factory.

Creates an Azure AI Foundry agent with multiple capabilities:
- Bing Grounding Search for web information
- File Search for document retrieval
- Code Interpreter for Python execution
- Custom function tools (weather, time)
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from agent_framework import ChatAgent, HostedCodeInterpreterTool, HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

from app.agent_registry.config_loader import load_agent_config
from app.agent_registry.RealtimeAssistant.tools import get_time, get_weather
from utils.ml_logging import get_logger

logger = get_logger("app.agent_registry.RealtimeAssistant.main")


async def create_realtime_assistant() -> Tuple[ChatAgent, str, str, str]:
    """
    Create NEW Realtime Assistant agent with all tools (OFFLINE USE ONLY).

    This function creates everything from scratch:
    1. Uploads airport_operations.pdf to Azure AI
    2. Creates vector store with the file
    3. Creates Azure AI agent with all tools
    4. Returns agent and IDs for future reuse

    Run this ONCE offline, then use setup_realtime_assistant(agent_id) in production.

    :return: Tuple of (agent, agent_id, vector_store_id, file_id)
    :raises: Exception if creation fails
    """
    try:
        logger.info("=" * 80)
        logger.info("CREATING NEW Realtime Assistant agent")
        logger.info("=" * 80)

        # Load configuration
        logger.info("Loading configuration")
        config = load_agent_config("REALTIME_ASSISTANT")

        name = config["name"]
        description = config["description"]
        instructions = config["instructions"]
        endpoint = config["azure_ai_foundry"]["endpoint"]
        model_deployment = config["azure_ai_foundry"]["model_deployment"]

        # Get PDF file path
        pdf_file_path = Path("app/data/airport_operations.pdf")
        if not pdf_file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_file_path}")

        logger.info(f"PDF file located: {pdf_file_path}")

        # Initialize Azure clients
        logger.info("Initializing Azure clients")
        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        # Step 1: Upload PDF file
        logger.info(f"Uploading {pdf_file_path.name} to Azure AI")
        file = await project_client.agents.files.upload_and_poll(
            file_path=str(pdf_file_path), purpose="assistants"
        )
        logger.info(f"File uploaded - ID: {file.id}")

        # Step 2: Create vector store
        logger.info("Creating vector store")
        vector_store = await project_client.agents.vector_stores.create_and_poll(
            file_ids=[file.id], name="airline_ops_knowledge_base"
        )
        logger.info(f"Vector store created - ID: {vector_store.id}")

        # Step 3: Build tools list
        logger.info("Configuring tools")
        all_tools = []

        # Bing Search
        if config.get("bing_search", {}).get("enabled", False):
            bing_connection_id = os.getenv(
                config["bing_search"].get("connection_id_env", "BING_CONNECTION_ID")
            )
            if bing_connection_id:
                bing_tool = HostedWebSearchTool(
                    name=config["bing_search"].get("name", "Bing Grounding Search"),
                    description=config["bing_search"].get(
                        "description", "Search the web for current information"
                    ),
                    connection_id=bing_connection_id,
                )
                all_tools.append(bing_tool)
                logger.info("Bing Search tool added")

        # Code Interpreter
        code_interpreter = HostedCodeInterpreterTool(
            name="Python Code Interpreter",
            description="Execute Python code for calculations, data analysis, and problem solving",
        )
        all_tools.append(code_interpreter)
        logger.info("Code Interpreter tool added")

        # File Search with vector store
        from agent_framework import HostedFileSearchTool

        file_search_tool = HostedFileSearchTool(vector_store_ids=[vector_store.id])
        all_tools.append(file_search_tool)
        logger.info(f"File Search tool added with vector store: {vector_store.id}")

        # Custom function tools
        all_tools.append(get_weather)
        all_tools.append(get_time)
        logger.info("Custom function tools added (weather, time)")

        logger.info(f"Total tools configured: {len(all_tools)}")

        # Step 4: Create Azure AI agent
        logger.info(f"Creating Azure AI agent: {name}")
        azure_ai_agent = await project_client.agents.create_agent(
            model=model_deployment,
            name=name,
            instructions=instructions,
            tools=all_tools,
        )
        agent_id = azure_ai_agent.id
        logger.info(f"Agent created - ID: {agent_id}")

        # Step 5: Create ChatAgent wrapper
        logger.info("Creating ChatAgent wrapper")
        chat_client = AzureAIAgentClient(
            project_client=project_client, agent_id=agent_id
        )

        agent = ChatAgent(
            chat_client=chat_client,
            name=f"{name}Agent",
            description=description,
            instructions=instructions,
            tools=all_tools,
            user_approves_function_calls=False,
        )

        logger.info("=" * 80)
        logger.info("SUCCESS - Realtime Assistant created")
        logger.info("=" * 80)
        logger.info(f"Agent ID: {agent_id}")
        logger.info(f"Vector Store ID: {vector_store.id}")
        logger.info(f"File ID: {file.id}")
        logger.info("=" * 80)
        logger.info("Add these to your .env file:")
        logger.info(f"REALTIME_ASSISTANT_AGENT_ID={agent_id}")
        logger.info(f"FILE_SEARCH_VECTOR_STORE_ID={vector_store.id}")
        logger.info(f"AIRLINE_OPS_FILE_ID={file.id}")
        logger.info("=" * 80)

        return agent, agent_id, vector_store.id, file.id

    except Exception as e:
        logger.error(f"Failed to create Realtime Assistant: {str(e)}")
        raise


async def setup_realtime_assistant(
    agent_id: Optional[str] = None,
) -> ChatAgent:
    """
    Connect to EXISTING Realtime Assistant agent (RUNTIME USE).

    This function connects to a pre-existing Azure AI agent by ID.
    It does NOT create a new agent or upload files.

    The agent must already exist (created with create_realtime_assistant()).
    This is the FAST path for production runtime.

    IMPORTANT: Uses AzureCliCredential (not passed credential) because Foundry agents
    require specific Azure CLI token scopes to execute function tools properly.

    :param agent_id: Azure AI agent ID. If not provided, reads from
                     REALTIME_ASSISTANT_AGENT_ID environment variable.
    :return: Configured ChatAgent instance
    :raises: Exception if agent_id not found or connection fails
    """
    try:
        logger.info("Connecting to existing Realtime Assistant agent")

        # Load configuration
        config = load_agent_config("REALTIME_ASSISTANT")

        name = config["name"]
        description = config["description"]
        instructions = config["instructions"]
        endpoint = config["azure_ai_foundry"]["endpoint"]

        # Get agent ID from parameter, config, or environment
        if not agent_id:
            agent_id = config["azure_ai_foundry"].get("agent_id")
        if not agent_id:
            agent_id = os.getenv("REALTIME_ASSISTANT_AGENT_ID")

        if not agent_id:
            raise ValueError(
                "agent_id not provided and REALTIME_ASSISTANT_AGENT_ID not set in environment. "
                "Run create_realtime_assistant() first to create the agent."
            )

        logger.info(f"Agent ID: {agent_id}")

        # Initialize Azure clients - ALWAYS use AzureCliCredential for Foundry agents
        # This is critical: Foundry agents need Azure CLI scopes to execute function tools
        logger.info(
            "Creating AzureCliCredential for Foundry agent (required for function tool execution)"
        )
        credential = AzureCliCredential()

        # Create AIProjectClient first (required for AzureAIAgentClient)
        logger.info(f"Creating AIProjectClient with endpoint: {endpoint}")
        from azure.ai.projects.aio import AIProjectClient

        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        # Connect to existing agent using project_client
        logger.info(f"Connecting to agent: {agent_id}")
        chat_client = AzureAIAgentClient(
            project_client=project_client,
            agent_id=agent_id,
            credential=credential,
        )

        # Create ChatAgent wrapper with name and description (matching notebook pattern)
        # Tools are already configured on the remote agent - don't define them here
        logger.info("Creating ChatAgent wrapper for existing agent")
        agent = ChatAgent(
            chat_client=chat_client,
            name=name,
            description=description,
            instructions=instructions,  # Local instructions combine with remote agent instructions
        )

        logger.info(f"Realtime Assistant '{name}' connected successfully")
        logger.info("Agent connected - tools are configured on the remote agent")

        return agent

    except Exception as e:
        logger.error(f"Failed to connect to Realtime Assistant: {str(e)}")
        raise


async def delete_realtime_assistant(agent_id: str) -> None:
    """
    Delete the Realtime Assistant agent from Azure AI.

    Use with caution as this operation is irreversible.

    :param agent_id: ID of the agent to delete
    :return: None
    :raises: Exception if deletion fails
    """
    try:
        config = load_agent_config("REALTIME_ASSISTANT")
        endpoint = config["azure_ai_foundry"]["endpoint"]

        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        await project_client.agents.delete_agent(agent_id)
        logger.info(f"Realtime Assistant agent deleted: {agent_id}")

    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise
