"""Airline Operations Assistant - Streamlit UI."""

import asyncio
import os
import sys

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from settings import (APP_SUBTITLE, APP_TITLE, CHAT_CONTAINER_HEIGHT,
                      CHAT_INPUT_PLACEHOLDER, PAGE_TITLE,
                      validate_configuration)

from app.agent_registry.AirlineIntelligentAssistant.main import \
    setup_airline_intelligent_assistant
from utils.ml_logging import get_logger

logger = get_logger("app.main")


def setup_environment():
    """Initialize session state and validate config."""
    if not validate_configuration():
        st.error("Missing required environment variables. Check your .env file.")
        st.stop()

    if "azure_credential" not in st.session_state:
        try:
            from azure.identity import InteractiveBrowserCredential

            st.session_state.azure_credential = InteractiveBrowserCredential()
        except Exception as e:
            logger.error(f"Failed to create Azure credential: {e}")
            st.error("Failed to initialize Azure authentication.")
            st.stop()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "conversation_thread" not in st.session_state:
        st.session_state.conversation_thread = None


async def setup_agent():
    """Initialize the agent (once per session)."""
    if "agent" not in st.session_state:
        try:
            logger.info("Initializing agent...")

            from app.agent_registry.AirlineOpsContext import \
                main as ops_context_module

            ops_context_module.set_azure_credential(st.session_state.azure_credential)

            agent = await setup_airline_intelligent_assistant(
                credential=st.session_state.azure_credential
            )
            st.session_state.agent = agent
            logger.info("Agent ready")
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise


async def process_query(query: str) -> str:
    """Process a user query and return the response."""
    logger.debug(f"Processing query: {query[:50]}...")

    agent = st.session_state.get("agent")
    if not agent:
        raise RuntimeError("Agent not initialized")

    if st.session_state.conversation_thread is None:
        st.session_state.conversation_thread = agent.get_new_thread()

    try:
        result = await agent.run(query, thread=st.session_state.conversation_thread)
        return result.text if hasattr(result, "text") else str(result)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise


def render_chat_history(chat_container):
    """Render conversation history."""
    if "chat_history" not in st.session_state:
        return

    for msg in st.session_state.chat_history:
        role = msg["role"].lower()
        content = msg["content"]

        if role == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(content, unsafe_allow_html=True)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content, unsafe_allow_html=True)


def render_header():
    """Render the app header."""
    st.markdown(
        f"""
        <style>
        .header {{
            text-align: center;
            background: linear-gradient(145deg, #1F6095, #008AD7);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ margin: 0; font-size: 1.8rem; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; }}
        </style>
        <div class="header">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Main entry point."""
    st.set_page_config(page_title=PAGE_TITLE)
    setup_environment()

    try:
        asyncio.run(setup_agent())
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        st.error(f"Agent initialization failed: {e}")
        st.stop()

    render_header()

    user_input = st.chat_input(CHAT_INPUT_PLACEHOLDER)
    chat_container = st.container(height=CHAT_CONTAINER_HEIGHT)

    with chat_container:
        render_chat_history(chat_container)

        if user_input:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_input)

            with st.spinner("Processing..."):
                try:
                    result = asyncio.run(process_query(user_input))
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": result}
                    )
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(result, unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    st.error(f"Something went wrong: {e}")


if __name__ == "__main__":
    main()
