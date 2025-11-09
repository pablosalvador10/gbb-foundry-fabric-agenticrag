from agent_framework import (
    ChatAgent,
    WorkflowBuilder,
    MagenticBuilder,
    MagenticAgentDeltaEvent,
    MagenticAgentMessageEvent,
    MagenticFinalResultEvent,
    MagenticOrchestratorMessageEvent,
    WorkflowOutputEvent,
)

from agent_framework.microsoft import CopilotStudioAgent
from agent_framework.azure import AzureAIAgentClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

import os
from typing import Optional
from utils.ml_logging import get_logger

logger = get_logger()


def build_copilot_agent(
    name: Optional[str] = None, description: Optional[str] = None
) -> CopilotStudioAgent:
    """Create CopilotStudioAgent using environment config."""
    agent = CopilotStudioAgent(
        name=name,
        description=description,
    )
    return agent


async def build_foundry_agent(
    project,
    agent_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
) -> tuple[ChatAgent, AIProjectClient, AzureCliCredential]:
    """Attach to an existing Azure AI Foundry agent (preferred), or create one ad-hoc.
    Returns the agent and the clients that need to stay alive for the agent to work."""

    existing_id = agent_id or os.getenv("AZURE_AI_EXISTING_AGENT_ID")
    if not existing_id:

        logger.info(f"Using existing Foundry agent: {existing_id}")
        chat_client = AzureAIAgentClient(project_client=project, agent_id=existing_id)
        agent = ChatAgent(
            chat_client=chat_client,
            name=name or "FoundryAgent",
            description=description or "Fabric/Lakehouse/SQL/KPI agent.",
            instructions=instructions
            or "Answer with metrics/tables and add source hints.",
        )
        return agent
    else:
        logger.error(f"No existing Agents IDs")
        return
