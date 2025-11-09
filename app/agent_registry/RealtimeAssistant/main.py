"""
Realtime Assistant Agent Factory.

Creates an Azure AI Foundry agent with multiple capabilities:
- Bing Grounding Search for web information
- File Search for document retrieval
- Custom function tools (weather, time)
"""

import os
from typing import Optional

from agent_framework import (
    ChatAgent,
    HostedWebSearchTool,
    HostedFileSearchTool,
    HostedVectorStoreContent,
)
from agent_framework.azure import AzureAIAgentClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

from app.agent_registry.config_loader import load_agent_config
from app.agent_registry.RealtimeAssistant.tools import get_weather, get_time
from utils.ml_logging import get_logger

logger = get_logger("app.agent_registry.RealtimeAssistant.main")


async def setup_realtime_assistant() -> ChatAgent:
    """
    Initialize the Realtime Assistant agent with all capabilities.

    This function creates an Azure AI Foundry agent that combines:
    - Bing Grounding Search for real-time web information
    - File Search for document retrieval
    - Custom function tools (weather, time)

    The agent can reuse an existing agent ID from configuration or create a new one.

    :return: Configured ChatAgent instance ready to use as a tool
    :raises: Exception if agent creation fails or required environment variables are missing
    """
    try:
        # Load dynamic configuration
        logger.info("Loading Realtime Assistant configuration...")
        config = load_agent_config("REALTIME_ASSISTANT_CONFIG")

        # Extract configuration values
        name = config["name"]
        description = config["description"]
        instructions = config["instructions"]

        # Azure AI Foundry settings
        endpoint = config["azure_ai_foundry"]["endpoint"]
        model_deployment = config["azure_ai_foundry"]["model_deployment"]
        agent_id = config["azure_ai_foundry"].get(
            "agent_id"
        )  # Optional - reuse existing

        # Initialize Azure clients
        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        # Build tools list
        tools = []

        # 1. Add Bing Search if enabled
        if config.get("bing_search", {}).get("enabled", False):
            logger.info("Adding Bing Grounding Search tool...")
            bing_connection_id = config["bing_search"].get("connection_id")

            if bing_connection_id:
                # Set environment variable for HostedWebSearchTool
                os.environ["BING_CONNECTION_ID"] = bing_connection_id

                bing_tool = HostedWebSearchTool(
                    name=config["bing_search"].get("name", "Bing Grounding Search"),
                    description=config["bing_search"].get(
                        "description", "Search the web for current information"
                    ),
                )
                tools.append(bing_tool)
                logger.info("Bing Search tool added successfully")
            else:
                logger.warning("Bing search enabled but no connection_id provided")

        # 2. Add File Search if enabled
        if config.get("file_search", {}).get("enabled", False):
            logger.info("Adding File Search tool...")
            vector_store_id = config["file_search"].get("vector_store_id")

            if vector_store_id:
                file_search_tool = HostedFileSearchTool(
                    inputs=[HostedVectorStoreContent(vector_store_id=vector_store_id)]
                )
                tools.append(file_search_tool)
                logger.info(
                    f"File Search tool added with vector store: {vector_store_id}"
                )
            else:
                logger.warning("File search enabled but no vector_store_id provided")

        # 3. Add custom function tools
        function_tools = []
        for tool_name in config.get("tools", []):
            if tool_name == "get_weather":
                function_tools.append(get_weather)
                logger.info("Added get_weather function tool")
            elif tool_name == "get_time":
                function_tools.append(get_time)
                logger.info("Added get_time function tool")
            else:
                logger.warning(f"Unknown tool '{tool_name}' in configuration")

        tools.extend(function_tools)

        logger.info(f"Total tools configured: {len(tools)}")

        # Create or reuse agent
        if agent_id:
            logger.info(f"Reusing existing agent with ID: {agent_id}")
            chat_client = AzureAIAgentClient(
                project_client=project_client, agent_id=agent_id
            )
        else:
            logger.info(f"Creating new agent: {name}")

            # Create new Azure AI Foundry agent with all tools
            azure_ai_agent = await project_client.agents.create_agent(
                model=model_deployment,
                name=name,
                instructions=instructions,
                tools=tools,  # All tools passed to remote agent
            )
            agent_id = azure_ai_agent.id
            logger.info(f"New agent created with ID: {agent_id}")
            logger.info(
                f"IMPORTANT: Store this agent_id in your .env file as REALTIME_ASSISTANT_AGENT_ID={agent_id}"
            )

            chat_client = AzureAIAgentClient(
                project_client=project_client, agent_id=agent_id
            )

        # Create ChatAgent wrapper
        agent = ChatAgent(
            chat_client=chat_client,
            name=f"{name}Agent",
            description=description,
            instructions=instructions,
            tools=tools,  # Tools also in wrapper for consistency
        )

        logger.info(f"Realtime Assistant agent '{name}' initialized successfully")
        logger.info(f"Agent capabilities: Bing Search, File Search, Weather, Time")

        return agent

    except KeyError as e:
        logger.error(f"Missing required configuration key: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create Realtime Assistant agent: {str(e)}")
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
        config = load_agent_config("REALTIME_ASSISTANT_CONFIG")
        endpoint = config["azure_ai_foundry"]["endpoint"]

        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        await project_client.agents.delete_agent(agent_id)
        logger.info(f"Realtime Assistant agent deleted: {agent_id}")

    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise
