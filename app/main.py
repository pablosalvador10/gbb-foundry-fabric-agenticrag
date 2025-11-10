"""
Airline Operations Assistant - Streamlit Application.

This module serves as the main entry point for the Streamlit UI, providing
a clean interface to the AirlineIntelligentAssistant multi-agent system.
"""

import asyncio
from typing import Any

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
from app.agent_registry.AirlineIntelligentAssistant.main import (
    setup_airline_intelligent_assistant,
)
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
        logger.info("🔧 Setting up environment and initializing session state")

        if not validate_configuration():
            logger.error("Missing required environment variables")
            st.error(
                "Missing required environment variables. Please check your .env file."
            )
            st.stop()

        # Initialize Azure authentication once for the entire session
        if "azure_credential" not in st.session_state:
            from azure.identity import InteractiveBrowserCredential
            logger.info("🔐 Initializing Azure authentication (browser login)...")
            logger.info("📢 A browser window will open for authentication...")
            st.session_state.azure_credential = InteractiveBrowserCredential()
            logger.info("✅ Azure authentication initialized successfully")

        if not validate_configuration():
            logger.error("Missing required environment variables")
            st.error(
                "Missing required environment variables. Please check your .env file."
            )
            st.stop()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            logger.info("Initialized chat_history in session state")

        if "conversation_thread" not in st.session_state:
            st.session_state.conversation_thread = None
            logger.info("Initialized conversation_thread in session state")

    except Exception as e:
        logger.error(f"Error during environment setup: {str(e)}")
        st.error(f"Environment setup failed: {str(e)}")
        st.stop()


async def setup_agent() -> None:
    """
    Initialize the Airline Intelligent Assistant agent.

    This function creates the main orchestrator agent and stores it in session state.
    The agent is initialized only once per session and reused across all queries.

    Components initialized:
    - AirlineIntelligentAssistant: Main orchestrator with two sub-agents as tools
      - AirlineOpsContext: For operational data from Microsoft Fabric
      - RealtimeAssistant: For web search, weather, time, and file search

    :return: None
    :raises: Exception if agent initialization fails
    """
    if "agent" not in st.session_state:
        try:
            logger.info("🤖 Initializing Airline Intelligent Assistant...")
            
            # Pass the cached credential to the agent modules
            from app.agent_registry.AirlineOpsContext import main as ops_context_module
            ops_context_module.set_azure_credential(st.session_state.azure_credential)
            
            agent = await setup_airline_intelligent_assistant()
            st.session_state.agent = agent
            logger.info("✅ Airline Intelligent Assistant initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error during agent setup: {str(e)}")
            raise


async def process_query(query: str) -> str:
    """
    Process a user query with the Airline Intelligent Assistant.

    This function handles:
    1. Thread creation for first query (conversation memory)
    2. Query execution with the agent (tools auto-approved for efficiency)
    3. Response extraction

    Azure OpenAI models support parallel tool calling natively - when multiple
    tools can be executed independently, they run concurrently automatically.

    Args:
        query: User's question or request

    Returns:
        Agent's response text

    :raises: Exception if query processing fails
    """
    logger.info("=" * 100)
    logger.info("🚀 STARTING QUERY PROCESSING")
    logger.info(f"💬 User Query: {query}")
    logger.info("=" * 100)

    try:
        # Get agent from session state
        agent = st.session_state.get("agent")
        if not agent:
            raise RuntimeError("Agent not initialized. Please refresh the page.")

        # Get or create conversation thread for memory persistence
        if st.session_state.conversation_thread is None:
            logger.info("🆕 Creating new conversation thread for session")
            st.session_state.conversation_thread = agent.get_new_thread()
        else:
            logger.info("♻️  Using existing conversation thread (memory enabled)")

        thread = st.session_state.conversation_thread

        # Execute query with agent using persistent thread
        logger.info("🤖 EXECUTING WITH: AirlineIntelligentAssistant (Main Orchestrator)")
        logger.info("📡 Available sub-agents: AirlineOpsContext, RealtimeAssistant")
        logger.info("⚡ Tools auto-approved - parallel execution enabled")
        
        # Simple execution - no approval loop needed
        result = await agent.run(query, thread=thread)

        # Extract response text
        response_text = result.text if hasattr(result, "text") else str(result)

        logger.info("✅ Query processed successfully")
        logger.info("=" * 100)
        return response_text

    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        logger.info("=" * 100)
        raise


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
    Main entry point for the Airline Operations Assistant.

    Orchestrates the entire application flow:
    - Initializes environment and agent
    - Renders the user interface
    - Handles user queries with conversation memory
    - Displays results and maintains conversation history
    """
    try:
        logger.info("Starting Airline Operations Assistant app")

        # Set page config first (must be called before other Streamlit commands)
        st.set_page_config(page_title=PAGE_TITLE)

        # Initialize environment - CRITICAL: This must happen early
        setup_environment()

        # Initialize agent asynchronously (only once per session)
        asyncio.run(setup_agent())

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

                # Process with agent
                with st.spinner("Processing with Airline Intelligent Assistant..."):
                    try:
                        # Execute query with agent (with conversation memory)
                        result = asyncio.run(process_query(user_input))

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
