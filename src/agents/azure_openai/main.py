from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from utils.ml_logging import get_logger

logger = get_logger("agent_registry.azure_openai.main")


def setup_aoai_agent(
    name: str,
    endpoint: str,
    api_key: str,
    deployment_name: str,
    tools: list,
    instructions: str,
    description: str,
) -> ChatAgent:
    """
    Initialize an Azure OpenAI ChatAgent with specified configuration.

    This function creates a ChatAgent configured with the provided tools,
    instructions, and Azure OpenAI endpoint settings.

    :param name: Agent name identifier
    :param endpoint: Azure OpenAI endpoint URL
    :param api_key: Azure OpenAI API key for authentication
    :param deployment_name: Azure OpenAI model deployment name
    :param tools: List of callable tools available to the agent
    :param instructions: System instructions defining agent behavior
    :param description: Agent description for identification
    :return: Configured ChatAgent instance
    :raises: Exception if agent creation fails
    """
    try:
        agent = ChatAgent(
            chat_client=AzureOpenAIChatClient(
                endpoint=endpoint,
                api_key=api_key,
                deployment_name=deployment_name,
            ),
            name=f"{name}Agent",
            description=description,
            instructions=instructions,
            tools=tools,
        )
        logger.info(f"Azure OpenAI ChatAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Azure OpenAI ChatAgent '{name}': {str(e)}")
        raise
