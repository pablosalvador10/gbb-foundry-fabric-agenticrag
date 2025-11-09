"""
Multi-Agent Streamlit Application for R&D Intelligence.

This module serves as the main entry point that orchestrates the Streamlit UI
and intelligent agent routing for the enterprise multi-agent system.
"""

import asyncio
from typing import Any, Dict, Tuple

import streamlit as st

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from settings import (
    PAGE_TITLE,
    APP_TITLE,
    APP_SUBTITLE,
    CHAT_CONTAINER_HEIGHT,
    CHAT_INPUT_PLACEHOLDER,
    validate_configuration,
)
from agents.foundry.foundryagents import (
    initialize_foundry_services,
    get_foundry_agent,
    is_foundry_agent_available,
)
from app.agents.azure_openai.dataagents import (
    initialize_fabric_services,
    get_unified_fabric_agent,
    is_unified_fabric_agent_available,
)
from agents.azure_openai.intelligent_orchestrator import get_orchestrator
from utils.ml_logging import get_logger

logger = get_logger("app.main")


def setup_environment() -> None:
    """
    Initialize environment variables and Streamlit session state.

    This function performs critical initialization tasks including environment
    variable validation and session state setup for conversation persistence.

    :return: None
    :raises: SystemExit if required environment variables are missing
    """
    try:
        logger.info("Setting up environment and initializing session state")

        if not validate_configuration():
            logger.error("Missing required environment variables")
            st.error(
                "Missing required environment variables. Please check your .env file."
            )
            st.stop()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            logger.info("Initialized chat_history in session state")

    except Exception as e:
        logger.error(f"Error during environment setup: {str(e)}")
        st.error(f"Environment setup failed: {str(e)}")
        st.stop()


def setup_agents() -> None:
    """
    Initialize all AI agents for the multi-agent system.

    This function orchestrates the initialization of all specialized AI agents
    including Fabric Data Agents, Foundry agents, and the intelligent orchestrator
    for semantic routing capabilities.

    Components initialized:
    - Fabric Data Agent clients for structured data queries (agent_registry.azure_openai.fabric)
    - Foundry agent for FedEx ETD expertise (agent_registry.foundry.foundryagents)
    - Unified Fabric agent with multiple data source tools (agent_registry.azure_openai.fabric)
    - Intelligent orchestrator for semantic routing (agent_registry.azure_openai.intelligent_orchestrator)

    :return: None
    :raises: Exception if agent initialization fails
    """
    try:
        logger.info("Initializing all agent services")
        initialize_fabric_services()
        initialize_foundry_services()

        orchestrator = get_orchestrator()
        logger.info("All agents and orchestrator setup completed successfully")

    except Exception as e:
        logger.error(f"Error during agent setup: {str(e)}")
        raise


async def get_intelligent_routing_decision(query: str) -> Dict[str, str]:
    """
    Use intelligent semantic routing to determine the optimal agent.

    Args:
        query: User's question or request

    Returns:
        Dictionary containing agent selection details from intelligent analysis
    """
    orchestrator = get_orchestrator()

    # Get the routing decision from the intelligent orchestrator
    agent_name, reasoning, routing_info = await orchestrator.route_query(query)

    return routing_info


async def production_agent_system(query: str) -> Tuple[str, Dict[str, str]]:
    """
    Production-ready multi-agent system with intelligent semantic routing.

    This is the core function that:
    1. Uses AI to analyze the user query semantically
    2. Routes the query to the most appropriate specialized agent
    3. Returns the response with routing decision details

    Args:
        query: User's question or request

    Returns:
        Tuple containing:
        - Agent's response text
        - Routing decision dictionary with metadata
    """
    logger.info(f"Processing query: {query}")

    try:
        # Get the agents from their respective registry locations
        foundry_agent = (
            get_foundry_agent() if is_foundry_agent_available() else None
        )  # agent_registry.foundry.foundryagents
        fabric_agent = (
            get_unified_fabric_agent() if is_unified_fabric_agent_available() else None
        )  # agent_registry.azure_openai.fabric

        # Check if we have the required agents
        if not foundry_agent:
            logger.warning(
                "Foundry agent not available (agent_registry.foundry.foundryagents)"
            )
        if not fabric_agent:
            logger.warning(
                "Fabric agent not available (agent_registry.azure_openai.fabric)"
            )

        if not foundry_agent and not fabric_agent:
            return "❌ No agents available. Please check your configuration.", {
                "agent": "none",
                "name": "No Agent",
                "icon": "❌",
                "purpose": "Error - No agents available",
                "reasoning": "System configuration error",
                "confidence": "error",
            }

        # Use the intelligent orchestrator for routing and execution
        orchestrator = get_orchestrator()
        orchestrator.set_agents(foundry_agent, fabric_agent)

        response_text, routing_decision = await orchestrator.execute_query(query)

        logger.info(
            f"Intelligent routing: {routing_decision['name']} - {routing_decision['reasoning']}"
        )
        return response_text, routing_decision

    except Exception as e:
        logger.error(f"Error in intelligent agent system: {str(e)}")
        return f"❌ Error in intelligent routing: {str(e)}", {
            "agent": "error",
            "name": "System Error",
            "icon": "❌",
            "purpose": "Error handling",
            "reasoning": f"System error: {str(e)}",
            "confidence": "error",
        }


def render_chat_history(chat_container: Any) -> None:
    """
    Render the conversation history in the Streamlit interface.

    Displays all previous messages from users, assistants, and system info
    with appropriate avatars and formatting.

    Args:
        chat_container: Streamlit container for chat display
    """
    logger.debug("Rendering chat history.")

    # Defensive check - ensure chat_history exists before accessing
    if "chat_history" not in st.session_state:
        logger.warning("Chat history not initialized yet, skipping render")
        return

    for msg in st.session_state.chat_history:
        role = msg["role"].lower()
        content = msg["content"]
        avatar = msg.get("avatar", "🤖")

        if role == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(content, unsafe_allow_html=True)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content, unsafe_allow_html=True)
        elif role in ("info", "system"):
            st.info(content, icon=avatar)


def render_ui_header() -> None:
    """Render the application header with title and styling."""
    st.markdown(
        f"""
        <style>
        .titleContainer {{
            text-align: center;
            background: linear-gradient(145deg, #1F6095, #008AD7);
            color: #FFFFFF;
            padding: 35px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }}
        .titleContainer h1 {{
            margin: 0;
            font-size: 2rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 600;
            color: #FFFFFF;
            letter-spacing: 0.8px;
        }}
        .titleContainer h3 {{
            margin: 8px 0 0;
            font-size: 1rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 400;
            color: #FFFFFF;
        }}
        </style>
        <div class="titleContainer">
            <h1>{APP_TITLE}</h1>
            <h3>{APP_SUBTITLE}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """
    Main entry point for the R&D Intelligent Multi-Agent Assistant.

    Orchestrates the entire application flow:
    - Initializes environment and agents
    - Renders the user interface
    - Handles user queries with intelligent agent routing
    - Displays results and maintains conversation history
    """
    try:
        logger.info("Starting R+D Intelligent Multi-Agent Assistant app.")

        # Set page config first (must be called before other Streamlit commands)
        st.set_page_config(page_title=PAGE_TITLE)

        # Initialize environment and agents - CRITICAL: This must happen early
        setup_environment()
        setup_agents()

        # Render UI header
        render_ui_header()

        # Chat interface
        user_input = st.chat_input(CHAT_INPUT_PLACEHOLDER)
        chat_container = st.container(height=CHAT_CONTAINER_HEIGHT)

        with chat_container:
            render_chat_history(chat_container)

            if user_input:
                # Add user message to chat history
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input, "avatar": "🧑‍💻"}
                )

                # Display user message
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(user_input, unsafe_allow_html=True)

                # Show processing status
                with st.status(
                    "🧠 Analyzing query with AI orchestrator...", expanded=True
                ) as status:
                    st.write("**Intelligent Semantic Analysis in Progress**")
                    st.write("• Analyzing query intent and context...")
                    st.write("• Determining optimal specialized agent...")
                    status.update(label="✅ AI analysis complete", state="complete")

                # Process with intelligent agent system
                with st.spinner("Processing with intelligent agent orchestrator..."):
                    try:
                        # Use intelligent production agent system
                        result, routing_decision = asyncio.run(
                            production_agent_system(user_input)
                        )

                        # Create intelligent routing summary for chat history
                        agent_selection_msg = f"""
**{routing_decision.get('icon', '🤖')} AI Orchestrator Decision: {routing_decision.get('name', 'Unknown Agent')}**
- **Purpose**: {routing_decision.get('purpose', 'Not specified')}  
- **AI Reasoning**: {routing_decision.get('reasoning', 'Semantic analysis')}
- **Confidence**: {routing_decision.get('confidence', 'Unknown')}
                        """

                        # Add agent selection info to chat history
                        st.session_state.chat_history.append(
                            {
                                "role": "info",
                                "content": agent_selection_msg.strip(),
                                "avatar": "🎯",
                            }
                        )

                        # Add assistant response to chat history
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": result, "avatar": "🤖"}
                        )

                        # Display assistant message
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(result, unsafe_allow_html=True)

                    except Exception as e:
                        error_msg = f"Error processing request: {str(e)}"
                        logger.error(error_msg)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": error_msg, "avatar": "❌"}
                        )

                        with st.chat_message("assistant", avatar="❌"):
                            st.error(error_msg)

    except Exception as e:
        logger.error(f"Runtime error in main: {e}")
        st.error(f"Runtime error: {e}")
    finally:
        logger.info("App execution finished.")


def run() -> None:
    """Run the Streamlit app."""
    try:
        main()
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        st.error(f"Runtime error: {e}")


if __name__ == "__main__":
    run()
