"""
Airline Intelligent Assistant Agent Factory.

Main orchestrator that uses sub-agents as function tools through the .as_tool() pattern.
This agent coordinates between operational data retrieval and realtime assistance.
"""

import asyncio
from src.agents.azure_openai.main import setup_aoai_agent
from app.agent_registry.config_loader import load_agent_config
from app.agent_registry.AirlineOpsContext.main import airline_ops_context_agent
from app.agent_registry.RealtimeAssistant.main import setup_realtime_assistant
from utils.ml_logging import get_logger

logger = get_logger("app.agent_registry.AirlineIntelligentAssistant.main")


async def setup_airline_intelligent_assistant():
    """
    Initialize the Airline Intelligent Assistant main orchestrator.

    This agent coordinates between two specialized sub-agents:
    - AirlineOpsContext: For operational data from Microsoft Fabric
    - RealtimeAssistant: For web search, weather, time, and file search

    Both sub-agents are exposed as function tools using the .as_tool() pattern,
    allowing the main agent to automatically delegate queries to the appropriate sub-agent.

    :return: Configured ChatAgent instance
    :raises: Exception if agent creation fails or required environment variables are missing
    """
    try:
        # Load dynamic configuration
        logger.info("Loading Airline Intelligent Assistant configuration...")
        config = load_agent_config("AIRLINE_INTELLIGENT_ASSISTANT")

        # Extract configuration values
        name = config["name"]
        description = config["description"]
        instructions = config["instructions"]
        endpoint = config["azure_openai"]["endpoint"]
        api_key = config["azure_openai"]["api_key"]
        deployment = config["azure_openai"]["deployment"]

        logger.info("Initializing sub-agents...")

        # Initialize sub-agents
        # 1. AirlineOpsContext - Already initialized as module-level variable
        logger.info("Using AirlineOpsContext agent for operational data...")

        # 2. RealtimeAssistant - Create async
        logger.info("Creating RealtimeAssistant agent for realtime capabilities...")
        realtime_agent = await setup_realtime_assistant()

        # Convert sub-agents to tools using .as_tool()
        logger.info("Converting sub-agents to function tools...")

        ops_context_tool = airline_ops_context_agent.as_tool(
            name="AirlineOpsContext",
            description=(
                "Query operational data from Microsoft Fabric including flights, baggage, "
                "routes, airports, and SLA metrics. Use this for airline operational data queries."
            ),
            arg_name="query",
            arg_description="The operational question about flights, baggage, routes, airports, or SLAs",
        )

        realtime_tool = realtime_agent.as_tool(
            name="RealtimeAssistant",
            description=(
                "Access real-time information including web search (Bing), weather data, "
                "current time, and document search. Use this for current events, weather, "
                "time queries, or web searches."
            ),
            arg_name="query",
            arg_description="The query for web search, weather, time, or document search",
        )

        logger.info("Creating main orchestrator agent...")

        # Create main orchestrator with sub-agents as tools
        main_agent = setup_aoai_agent(
            name=name,
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=deployment,
            tools=[ops_context_tool, realtime_tool],
            instructions=instructions,
            description=description,
        )

        logger.info(f"Airline Intelligent Assistant '{name}' initialized successfully")
        logger.info("Main agent has access to: AirlineOpsContext, RealtimeAssistant")

        return main_agent

    except KeyError as e:
        logger.error(f"Missing required configuration key: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create Airline Intelligent Assistant: {str(e)}")
        raise


# Example usage
async def main():
    """
    Example usage of the Airline Intelligent Assistant with thread persistence.
    
    Thread management enables conversation memory across multiple queries,
    allowing the agent to maintain context and reference previous interactions.
    """
    agent = await setup_airline_intelligent_assistant()

    # Create a persistent thread for the conversation session
    # This enables the agent to remember context across multiple queries
    thread = agent.get_new_thread()

    # Example queries - agent maintains context across all queries in the thread
    queries = [
        "What flights are delayed right now at ORD?",
        "What's the weather like in New York?",
        "Show me baggage handling performance for last week",
        "What time is it in UTC?",
        "Can you summarize what I asked about?",  # Tests memory
    ]

    print("=== Conversation with Persistent Memory ===\n")
    for query in queries:
        print(f"User: {query}")
        # Pass the same thread to maintain conversation context
        result = await agent.run(query, thread=thread)
        print(f"Agent: {result.text}\n")


if __name__ == "__main__":
    asyncio.run(main())
