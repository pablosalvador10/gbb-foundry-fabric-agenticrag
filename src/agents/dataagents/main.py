"""
Fabric Agent Management Module
Handles Fabric Data agents
"""

import time
import uuid
from typing import Optional

from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._utils import is_given
from azure.identity import DefaultAzureCredential

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from utils.ml_logging import get_logger

logger = get_logger("src.agents.dataagents")

# ---- FABRIC CONFIGURATION ----
FABRIC_SCOPE: str = "https://api.fabric.microsoft.com/.default"
FABRIC_API_VERSION: str = "2024-05-01-preview"
DEFAULT_POLL_INTERVAL_SEC: int = 2
DEFAULT_TIMEOUT_SEC: int = 300


class DataAgent(OpenAI):
    """
    OpenAI client wrapper for Microsoft Fabric Data Agents.

    This class extends the OpenAI client to work with Fabric's AI Assistant API endpoints,
    handling authentication and request formatting specific to Fabric services.
    """

    def __init__(
        self, base_url: str, api_version: str = FABRIC_API_VERSION, default_headers: dict = None, **kwargs
    ) -> None:
        self.api_version = api_version
        self._auth_headers = default_headers or {}
        default_query = kwargs.pop("default_query", {})
        default_query["api-version"] = self.api_version
        super().__init__(
            api_key="",  # Not used, auth via bearer token
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
        headers.update(self._auth_headers)
        headers.setdefault("Accept", "application/json")
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)


def ask_fabric_agent(
    endpoint: str,
    question: str,
    credential=None,
    poll_interval_sec: int = DEFAULT_POLL_INTERVAL_SEC,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> str:
    """
    Query a Microsoft Fabric Data Agent with a question.

    This function sends a question to the specified Fabric Data Agent endpoint and
    polls for the response, handling the complete request-response cycle.

    :param endpoint: Fabric AI Assistant API endpoint URL
    :param question: The question to ask the agent
    :param credential: Optional Azure credential (reuses if provided, creates new if not)
    :param poll_interval_sec: How often to check run status in seconds
    :param timeout_sec: Maximum time to wait for response in seconds
    :return: The agent's text response or error message
    :raises: TimeoutError if polling exceeds timeout limit
    """
    try:
        logger.info(f"🔍 Querying Fabric agent at endpoint: {endpoint}")

        # Use provided credential or create new one
        if credential is None:
            logger.info("🔐 Creating new Azure credential...")
            credential = DefaultAzureCredential()
        else:
            logger.info("♻️  Reusing cached Azure credential")
        
        token = credential.get_token(FABRIC_SCOPE).token

        # Create Data Agent client
        client = DataAgent(base_url=endpoint, default_headers={"Authorization": f"Bearer {token}"})

        # Create assistant and thread
        assistant = client.beta.assistants.create(model="not-used")
        thread = client.beta.threads.create()

        try:
            # Send message
            client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=question
            )

            # Create and poll run
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

            # Extract response
            msgs = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
            out_chunks = []
            for m in msgs.data:
                if m.role == "assistant":
                    for c in m.content:
                        if getattr(c, "type", None) == "text":
                            out_chunks.append(c.text.value)

            response = "\n".join(out_chunks).strip() or "[No text content returned]"
            logger.info("Fabric agent query completed successfully")
            return response

        finally:
            try:
                client.beta.threads.delete(thread_id=thread.id)
            except Exception:
                pass

    except Exception as e:
        error_msg = f"Error querying Fabric agent: {str(e)}"
        logger.error(error_msg)
        return error_msg
