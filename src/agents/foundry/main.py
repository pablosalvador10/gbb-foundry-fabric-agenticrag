"""
Foundry Agent Factory Module.

This module provides utilities to create and manage Azure AI Foundry agents,
handling agent creation, ID persistence, and agent reuse patterns.
"""

from typing import Optional, List, Callable
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from utils.ml_logging import get_logger

logger = get_logger("src.agents.foundry.main")


async def setup_foundry_agent(
    name: str,
    endpoint: str,
    model_deployment: str,
    tools: List[Callable],
    instructions: str,
    description: str,
    agent_id: Optional[str] = None,
) -> tuple[ChatAgent, str]:
    """
    Initialize an Azure AI Foundry ChatAgent with specified configuration.

    This function either creates a new Foundry agent or reuses an existing one
    based on the provided agent_id. When creating a new agent, the returned
    agent_id should be stored in configuration for future reuse.

    :param name: Agent name identifier
    :param endpoint: Azure AI Project endpoint URL
    :param model_deployment: Azure OpenAI model deployment name
    :param tools: List of callable tools available to the agent
    :param instructions: System instructions defining agent behavior
    :param description: Agent description for identification
    :param agent_id: Optional existing agent ID to reuse (if None, creates new)
    :return: Tuple of (Configured ChatAgent instance, agent_id)
    :raises: Exception if agent creation fails
    """
    try:
        # Initialize Azure AI Project Client
        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        # If agent_id provided, reuse existing agent
        if agent_id:
            logger.info(f"Reusing existing Foundry agent with ID: {agent_id}")
            chat_client = AzureAIAgentClient(
                project_client=project_client, agent_id=agent_id
            )
        else:
            # Create new Foundry agent with tools
            logger.info(f"Creating new Foundry agent: {name}")

            azure_ai_agent = await project_client.agents.create_agent(
                model=model_deployment,
                name=name,
                instructions=instructions,
                tools=tools,
            )
            agent_id = azure_ai_agent.id
            logger.info(f"New Foundry agent created with ID: {agent_id}")

            chat_client = AzureAIAgentClient(
                project_client=project_client, agent_id=agent_id
            )

        # Create ChatAgent wrapper instance
        agent = ChatAgent(
            chat_client=chat_client,
            name=f"{name}Agent",
            description=description,
            instructions=instructions,
            tools=tools,
        )

        logger.info(f"Azure AI Foundry ChatAgent '{name}' initialized successfully")
        return agent, agent_id

    except Exception as e:
        logger.error(f"Failed to create Azure AI Foundry ChatAgent '{name}': {str(e)}")
        raise


async def delete_foundry_agent(endpoint: str, agent_id: str) -> None:
    """
    Delete an Azure AI Foundry agent.

    This function removes a Foundry agent from Azure AI services.
    Use with caution as this operation is irreversible.

    :param endpoint: Azure AI Project endpoint URL
    :param agent_id: ID of the agent to delete
    :return: None
    :raises: Exception if agent deletion fails
    """
    try:
        credential = AzureCliCredential()
        project_client = AIProjectClient(endpoint=endpoint, credential=credential)

        await project_client.agents.delete_agent(agent_id)
        logger.info(f"Foundry agent deleted successfully: {agent_id}")

    except Exception as e:
        logger.error(f"Failed to delete Foundry agent {agent_id}: {str(e)}")
        raise
