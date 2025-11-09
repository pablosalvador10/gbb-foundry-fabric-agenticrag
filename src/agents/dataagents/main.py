"""
Fabric Agent Management Module
Handles Fabric Data agents
"""

import time
import uuid
import streamlit as st
from typing import Optional

from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._utils import is_given

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.settings import (
    FABRIC_SCOPE,
    FABRIC_API_VERSION,
    DEFAULT_POLL_INTERVAL_SEC,
    DEFAULT_TIMEOUT_SEC,
)
from utils.ml_logging import get_logger

logger = get_logger("agent_registry.azure_openai.fabric")


class DataAgent(OpenAI):
    """
    OpenAI client wrapper for Microsoft Fabric Data Agents.

    This class extends the OpenAI client to work with Fabric's AI Assistant API endpoints,
    handling authentication and request formatting specific to Fabric services.
    """

    def __init__(
        self, base_url: str, api_version: str = FABRIC_API_VERSION, **kwargs
    ) -> None:
        self.api_version = api_version
        default_query = kwargs.pop("default_query", {})
        default_query["api-version"] = self.api_version
        super().__init__(
            api_key="",
            base_url=base_url,
            default_query=default_query,
            **kwargs,
        )

    def _prepare_options(self, options: FinalRequestOptions) -> None:
        """
        Prepare request options with Fabric-specific authentication and headers.

        Args:
            options: Request options to be modified with auth headers
        """
        headers = {**options.headers} if is_given(options.headers) else {}
        headers[
            "Authorization"
        ] = f"Bearer {st.session_state.cred.get_token(FABRIC_SCOPE).token}"
        headers.setdefault("Accept", "application/json")
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)


def setup_fabric_clients(fabric_endpoints: Optional[dict[str, str]] = None) -> None:
    """
    Initialize Fabric Data Agent clients for different data sources.

    This function creates FabricOpenAI clients for product discovery, sales data,
    and airport information services, storing them in session state.

    :return: None
    :raises: Exception if client creation fails
    """
    if "fabric_clients" not in st.session_state:
        logger.info("Creating Fabric clients")
        st.session_state.fabric_clients = {}

        if st.session_state.cred is None:
            logger.warning("Fabric credentials not available, skipping Fabric clients")
            return

        try:
            for agent_type, url in fabric_endpoints.items():
                st.session_state.fabric_clients[agent_type] = DataAgent(base_url=url)
                logger.info(f"Created {agent_type} client successfully")
        except Exception as e:
            logger.error(f"Failed to create Fabric client: {str(e)}")
            raise


def ask_fabric_agent(
    agent_type: str,
    question: str,
    poll_interval_sec: int = DEFAULT_POLL_INTERVAL_SEC,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> str:
    """
    Query a Microsoft Fabric Data Agent with a question.

    This function sends a question to the specified Fabric Data Agent and
    polls for the response, handling the complete request-response cycle.

    :param agent_type: Type of agent ('product_discovery', 'sales_data', 'airport_info')
    :param question: The question to ask the agent
    :param poll_interval_sec: How often to check run status in seconds
    :param timeout_sec: Maximum time to wait for response in seconds
    :return: The agent's text response or error message
    :raises: TimeoutError if polling exceeds timeout limit
    """
    if agent_type not in st.session_state.fabric_clients:
        return f"[Error: Unknown agent type '{agent_type}']"

    client = st.session_state.fabric_clients[agent_type]
    logger.info(f"Routing query to {agent_type} agent")

    assistant = client.beta.assistants.create(model="not-used")
    thread = client.beta.threads.create()

    try:
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=question
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id
        )

        terminal = {"completed", "failed", "cancelled", "requires_action"}
        start = time.time()
        while run.status not in terminal:
            if time.time() - start > timeout_sec:
                raise TimeoutError(f"Run polling exceeded {timeout_sec}s")
            time.sleep(poll_interval_sec)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status != "completed":
            return f"[Run ended: {run.status}]"

        msgs = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
        out_chunks = []
        for m in msgs.data:
            if m.role == "assistant":
                for c in m.content:
                    if getattr(c, "type", None) == "text":
                        out_chunks.append(c.text.value)
        return "\n".join(out_chunks).strip() or "[No text content returned]"

    finally:
        try:
            client.beta.threads.delete(thread_id=thread.id)
        except Exception:
            pass
