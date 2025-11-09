"""
Fabric Agent Management Module
Handles Fabric Data agents and unified agent setup with Azure OpenAI.
"""

import time
import uuid
import streamlit as st
from typing import Annotated
from pydantic import Field

from azure.identity import InteractiveBrowserCredential
from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._types import Omit
from openai._utils import is_given

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.settings import (
    FABRIC_ENDPOINTS, FABRIC_SCOPE, FABRIC_API_VERSION, 
    DEFAULT_POLL_INTERVAL_SEC, DEFAULT_TIMEOUT_SEC,
    UNIFIED_FABRIC_AGENT_INSTRUCTIONS,
    AZURE_OPENAI_API_ENDPOINT, AZURE_OPENAI_KEY, AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID
)
from utils.ml_logging import get_logger

logger = get_logger()


class FabricOpenAI(OpenAI):
    """
    OpenAI client wrapper for Microsoft Fabric Data Agents.
    
    This class extends the OpenAI client to work with Fabric's AI Assistant API endpoints,
    handling authentication and request formatting specific to Fabric services.
    """
    
    def __init__(self, base_url: str, api_version: str = FABRIC_API_VERSION, **kwargs) -> None:
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
        headers = ({**options.headers} if is_given(options.headers) else {})
        headers["Authorization"] = f"Bearer {st.session_state.cred.get_token(FABRIC_SCOPE).token}"
        headers.setdefault("Accept", "application/json") 
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)


def setup_fabric_credentials() -> None:
    """
    Initialize Fabric authentication credentials.
    
    Sets up Interactive Browser Credential for authenticating with Fabric services.
    """
    if 'cred' not in st.session_state:
        try:
            st.session_state.cred = InteractiveBrowserCredential()
            logger.info("✅ Initialized Fabric credentials")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Fabric credentials: {e}")
            st.session_state.cred = None


def setup_fabric_clients() -> None:
    """
    Initialize Fabric Data Agent clients for different data sources.
    
    Creates FabricOpenAI clients for product discovery, sales data, and airport info.
    """
    if "fabric_clients" not in st.session_state:
        logger.info("🔧 Creating Fabric clients...")
        st.session_state.fabric_clients = {}
        
        # Check if credentials are available
        if st.session_state.cred is None:
            logger.warning("❌ Fabric credentials not available, skipping Fabric clients")
        else:
            for agent_type, url in FABRIC_ENDPOINTS.items():
                try:
                    st.session_state.fabric_clients[agent_type] = FabricOpenAI(base_url=url)
                    logger.info(f"✅ Created {agent_type} client")
                except Exception as e:
                    logger.error(f"❌ Failed to create {agent_type} client: {e}")





def setup_unified_fabric_agent() -> None:
    """
    Initialize the Unified Fabric agent with access to multiple data sources.
    
    Creates a ChatAgent that can access product discovery, sales data, and airport info tools.
    """
    if "unified_agent" not in st.session_state:
        try:
            st.session_state.unified_agent = ChatAgent(
                chat_client=AzureOpenAIChatClient(
                    endpoint=AZURE_OPENAI_API_ENDPOINT,
                    api_key=AZURE_OPENAI_KEY,
                    deployment_name=AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID
                ),
                name="UnifiedFabricAgent",
                description="Multi-domain agent with access to product, sales, and airport data sources",
                instructions=UNIFIED_FABRIC_AGENT_INSTRUCTIONS,
                tools=[product_discovery_qna, sales_data_qna, airport_info_qna],
            )
            logger.info("✅ Created Unified Fabric agent")
        except Exception as e:
            logger.error(f"❌ Failed to create Unified Fabric agent: {e}")
            st.session_state.unified_agent = None


def ask_fabric_agent(
    agent_type: str, 
    question: str, 
    poll_interval_sec: int = DEFAULT_POLL_INTERVAL_SEC, 
    timeout_sec: int = DEFAULT_TIMEOUT_SEC
) -> str:
    """
    Query a Microsoft Fabric Data Agent with a question.
    
    Args:
        agent_type: Type of agent ('product_discovery', 'sales_data', 'airport_info')
        question: The question to ask the agent
        poll_interval_sec: How often to check run status (seconds)
        timeout_sec: Maximum time to wait for response (seconds)
        
    Returns:
        The agent's text response or error message
    """
    if agent_type not in st.session_state.fabric_clients:
        return f"[Error: Unknown agent type '{agent_type}']"
    
    client = st.session_state.fabric_clients[agent_type]
    logger.info(f"🤖 Routing to {agent_type} agent...")
    
    assistant = client.beta.assistants.create(model="not-used")
    thread = client.beta.threads.create()
    
    try:
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
        
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


def product_discovery_qna(
    question: Annotated[str, Field(description="Product discovery Q&A")]
) -> str:
    """Query enterprise product information via Fabric Data Agent."""
    return ask_fabric_agent("product_discovery", question)


def sales_data_qna(
    question: Annotated[str, Field(description="Sales analytics Q&A")]
) -> str:
    """Query enterprise sales analytics via Fabric Data Agent."""
    return ask_fabric_agent("sales_data", question)


def airport_info_qna(
    question: Annotated[str, Field(description="Airport facilities Q&A")]
) -> str:
    """Query airport facilities information via Fabric Data Agent."""
    return ask_fabric_agent("airport_info", question)


def initialize_copilot_services() -> None:
    """
    Initialize all Fabric-related services in the correct order.
    
    This function should be called during application startup to ensure
    all Fabric components are properly configured.
    """
    logger.info("🔧 Initializing Fabric services...")
    setup_fabric_credentials()
    setup_fabric_clients()
    setup_unified_fabric_agent()
    logger.info("✅ Fabric services initialization complete")


def get_unified_fabric_agent() -> ChatAgent:
    """
    Get the initialized Unified Fabric agent from session state.
    
    Returns:
        ChatAgent: The Unified Fabric agent, or None if not available
    """
    return st.session_state.get('unified_agent')


def is_unified_fabric_agent_available() -> bool:
    """
    Check if the Unified Fabric agent is properly initialized and available.
    
    Returns:
        bool: True if the agent is available, False otherwise
    """
    return st.session_state.get('unified_agent') is not None