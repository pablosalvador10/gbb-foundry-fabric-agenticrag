"""
Multi-Agent Streamlit Application for R&D Intelligence
Integrates Microsoft Agent Framework with Azure Fabric for enterprise data analysis.
"""

import asyncio
import os
import time
import uuid
from typing import Annotated, Any, Dict, Optional, Tuple

import dotenv
import streamlit as st
from pydantic import Field

# Microsoft Agent Framework
from agent_framework import ChatAgent, WorkflowOutputEvent, ChatMessage, Role
from agent_framework.microsoft import CopilotStudioAgent
from agent_framework.azure import AzureAIAgentClient, AzureOpenAIChatClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

# Fabric Integration
from azure.identity import InteractiveBrowserCredential
from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._types import Omit
from openai._utils import is_given

# Local imports
from utils.ml_logging import get_logger

# --- Logging ---
logger = get_logger()

# ---- FABRIC AGENT ENDPOINTS (from notebook 06) ----
FABRIC_ENDPOINTS = {
    "product_discovery": "https://msitapi.fabric.microsoft.com/v1/workspaces/409e30ce-b2ad-4c80-a54d-d645227322e4/aiskills/672fba68-a7d0-4c85-99e9-9ed6fe8ef1d1/aiassistant/openai",
    "sales_data": "https://msitapi.fabric.microsoft.com/v1/workspaces/409e30ce-b2ad-4c80-a54d-d645227322e4/aiskills/360ef9b6-c087-4e72-ab7c-f157007cda3a/aiassistant/openai", 
    "airport_info": "https://msitapi.fabric.microsoft.com/v1/workspaces/00ae18cb-e789-4d42-be8d-a5b47e524e22/aiskills/1d266d5d-cbbb-4099-9ef2-69fa875e4f89/aiassistant/openai"
}

SCOPE = "https://api.fabric.microsoft.com/.default"

class FabricOpenAI(OpenAI):
    """
    OpenAI client wrapper for Microsoft Fabric Data Agents.
    
    This class extends the OpenAI client to work with Fabric's AI Assistant API endpoints,
    handling authentication and request formatting specific to Fabric services.
    """
    
    def __init__(self, base_url: str, api_version: str = "2024-05-01-preview", **kwargs) -> None:
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
        headers["Authorization"] = f"Bearer {st.session_state.cred.get_token(SCOPE).token}"
        headers.setdefault("Accept", "application/json") 
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)

def ask_fabric_agent(
    agent_type: str, 
    question: str, 
    poll_interval_sec: int = 2, 
    timeout_sec: int = 300
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

def setup_environment() -> None:
    """
    Initialize environment variables and Streamlit session state.
    
    Sets up:
    - Environment variables from .env file
    - Chat history for conversation persistence  
    - Fabric authentication credentials
    - Azure AI Project client for Foundry services
    """
    logger.info("Setting up environment and initialising session state.")
    
    # Load environment variables
    dotenv.load_dotenv(".env", override=True)

    # Initialize chat history FIRST - this is critical for proper operation
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        logger.info("✅ Initialized chat_history")

    # Initialize credentials
    if 'cred' not in st.session_state:
        try:
            st.session_state.cred = InteractiveBrowserCredential()
            logger.info("✅ Initialized Fabric credentials")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Fabric credentials: {e}")
            st.session_state.cred = None

    # Initialize Foundry project client  
    if 'foundry_project' not in st.session_state:
        try:
            st.session_state.foundry_project = AIProjectClient(
                endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"], 
                credential=AzureCliCredential()
            )
            logger.info("✅ Initialized Foundry project client")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Foundry project: {e}")
            st.session_state.foundry_project = None

def setup_agents() -> None:
    """
    Initialize all AI agents for the multi-agent system.
    
    Creates:
    - Fabric Data Agent clients for structured data queries
    - Copilot Studio agent for real-time information
    - Foundry agent for document and knowledge management  
    - Unified Fabric agent with multiple data source tools
    """
    
    # Setup Fabric clients
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

    # Copilot Agent
    if "copilot_agent" not in st.session_state:
        try:
            st.session_state.copilot_agent = CopilotStudioAgent(
                name="CopilotStudioAgent",
                description="SharePoint/Graph/doc retrieval and Q&A.",
            )
            logger.info("✅ Created Copilot agent")
        except Exception as e:
            logger.error(f"❌ Failed to create Copilot agent: {e}")
            st.session_state.copilot_agent = None

    # Foundry Agent  
    if "foundry_agent" not in st.session_state:
        if st.session_state.foundry_project is None:
            logger.warning("❌ Foundry project not available, skipping Foundry agent")
            st.session_state.foundry_agent = None
        else:
            try:
                agent_id = "asst_BjfbCaFZh2ju28zEJkpWLe0E"
                chat_client = AzureAIAgentClient(project_client=st.session_state.foundry_project, agent_id=agent_id)
                st.session_state.foundry_agent = ChatAgent(
                    chat_client=chat_client,
                    name="FoundryAgent", 
                    description="Fabric/Lakehouse/SQL/KPI agent.",
                    instructions="Answer with metrics/tables and add source hints."
                )
                logger.info("✅ Created Foundry agent")
            except Exception as e:
                logger.error(f"❌ Failed to create Foundry agent: {e}")
                st.session_state.foundry_agent = None

    # Unified Fabric Agent
    if "unified_agent" not in st.session_state:
        try:
            st.session_state.unified_agent = ChatAgent(
                chat_client=AzureOpenAIChatClient(
                    endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    deployment_name=os.getenv("AZURE_AOAI_CHAT_MODEL_NAME_DEPLOYMENT_ID")
                ),
                name="UnifiedFabricAgent",
                description="Multi-domain agent with access to product, sales, and airport data sources",
                instructions=(
                    "You are a helpful assistant with access to specialized data sources. "
                    "If the user asks about PRODUCT discovery (catalogs, reviews, inventory, shopping, etc.), "
                    "call the `product_discovery_qna` tool. "
                    "If the user asks about SALES analytics (ARR, pipeline, bookings, forecast, revenue, etc.), "
                    "call the `sales_data_qna` tool. "
                    "If the user asks about AIRPORT information (terminals, services, amenities, operations), "
                    "call the `airport_info_qna` tool. "
                    "You can use multiple tools if the question spans multiple domains. "
                    "Otherwise, answer directly using your general knowledge."
                ),
                tools=[product_discovery_qna, sales_data_qna, airport_info_qna],
            )
            logger.info("✅ Created Unified Fabric agent")
        except Exception as e:
            logger.error(f"❌ Failed to create Unified Fabric agent: {e}")
            st.session_state.unified_agent = None

def build_router(copilot: CopilotStudioAgent, foundry: ChatAgent) -> ChatAgent:
    ask_copilot = copilot.as_tool(
        name="ask_copilot",
        description="Use for SharePoint/Graph/doc queries (policies, decks, PDFs, sites)."
    )
    ask_foundry = foundry.as_tool(
        name="ask_foundry",
        description="Use for Fabric/Lakehouse/SQL/dataset/KPI/metric queries."
    )
    return ChatAgent(
        name="Router",
        description="Routes the task to the right backend agent, can ask one clarifying question.",
        instructions=(
            "You are the Router. Pick exactly one tool. "
            "ask_copilot → documents/policies/SharePoint; "
            "ask_foundry → Fabric/KPIs/Lakehouse/SQL. "
            "If unclear, ask ONE clarifying question, then choose."
        ),
        tools=[ask_copilot, ask_foundry]
    )

def build_verifier() -> ChatAgent:
    return ChatAgent(
        name="Verifier",
        description="Fact-checks and cleans responses.",
        instructions=(
            "Validate the Router's answer. Remove unverifiable claims. "
            "Normalize formatting. Add brief source notes if available. "
            "If confidence < 0.6, ask a single clarifying question."
        ),
    )


def get_agent_routing_decision(query: str) -> Dict[str, str]:
    """
    Determine the optimal agent for handling a user query.
    
    Args:
        query: User's question or request
        
    Returns:
        Dictionary containing agent selection details:
        - agent: Selected agent type ('unified_fabric', 'foundry', or 'copilot')
        - name: Human-readable agent name
        - icon: Emoji icon for UI display
        - purpose: Brief description of agent's role
        - reasoning: Why this agent was selected
        - data_sources: What data this agent can access
    """
    q_lower = query.lower()
    
    # Keywords for each agent type
    fabric_keywords = ["sales", "revenue", "product", "mard", "glucose", "airport", "analytics", "metrics", "kpi"]
    foundry_keywords = ["sharepoint", "document", "policy", "pdf", "private", "doc", "file"]
    
    # Check for matches
    fabric_matches = [kw for kw in fabric_keywords if kw in q_lower]
    foundry_matches = [kw for kw in foundry_keywords if kw in q_lower]
    
    if fabric_matches:
        return {
            "agent": "unified_fabric",
            "name": "Unified Fabric Agent",
            "icon": "📊",
            "purpose": "Structured Data Analytics",
            "reasoning": "Query matches structured data and analytics patterns",
            "data_sources": "Product catalogs, Sales metrics, Glucose/MARD data, Airport information"
        }
    elif foundry_matches:
        return {
            "agent": "foundry", 
            "name": "Foundry Agent",
            "icon": "📁",
            "purpose": "Document & Knowledge Management",
            "reasoning": "Query matches document and knowledge retrieval patterns",
            "data_sources": "SharePoint documents, Policies, Private enterprise data"
        }
    else:
        return {
            "agent": "copilot",
            "name": "Copilot Agent", 
            "icon": "🌐",
            "purpose": "Real-time & Internet Data",
            "reasoning": "Query requires general knowledge and real-time information",
            "data_sources": "Live internet data, Current events, General knowledge"
        }

async def production_agent_system(query: str) -> Tuple[str, Dict[str, str]]:
    """
    Production-ready multi-agent system with intelligent routing.
    
    This is the core function that:
    1. Analyzes the user query to determine the best agent
    2. Routes the query to the selected agent
    3. Returns the response with routing decision details
    
    Args:
        query: User's question or request
        
    Returns:
        Tuple containing:
        - Agent's response text
        - Routing decision dictionary with metadata
    """
    logger.info(f"🔍 Query: {query}")
    
    # Get routing decision with reasoning
    routing_decision = get_agent_routing_decision(query)
    logger.info(f"🎯 Selected: {routing_decision['name']} - {routing_decision['reasoning']}")
    
    # Route to selected agent with defensive checks
    try:
        if routing_decision["agent"] == "unified_fabric":
            if st.session_state.unified_agent is None:
                return "❌ Unified Fabric agent not available. Please check your Azure OpenAI configuration.", routing_decision
            result = await st.session_state.unified_agent.run(query)
        elif routing_decision["agent"] == "foundry":
            if st.session_state.foundry_agent is None:
                return "❌ Foundry agent not available. Please check your Azure AI Project configuration.", routing_decision
            result = await st.session_state.foundry_agent.run(query)
        else:  # copilot
            if st.session_state.copilot_agent is None:
                return "❌ Copilot agent not available. Please check your Copilot Studio configuration.", routing_decision
            result = await st.session_state.copilot_agent.run(query)
        
        # Extract final text
        final_text = result.text if hasattr(result, 'text') else str(result)
        return final_text, routing_decision
        
    except Exception as e:
        logger.error(f"❌ Error in production_agent_system: {e}")
        return f"❌ Error processing query with {routing_decision['name']}: {str(e)}", routing_decision


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
        st.set_page_config(page_title="R+D Intelligent Multi-Agent Assistant")
        
        # Initialize environment and agents - CRITICAL: This must happen early
        setup_environment()
        setup_agents()
        st.markdown(
            """
            <style>
            .titleContainer {
                text-align: center;
                background: linear-gradient(145deg, #1F6095, #008AD7);
                color: #FFFFFF;
                padding: 35px;
                border-radius: 12px;
                margin-bottom: 25px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            }
            .titleContainer h1 {
                margin: 0;
                font-size: 2rem;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-weight: 600;
                color: #FFFFFF;
                letter-spacing: 0.8px;
            }
            .titleContainer h3 {
                margin: 8px 0 0;
                font-size: 1rem;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-weight: 400;
                color: #FFFFFF;
            }
            </style>
            <div class="titleContainer">
                <h1>Research Intelligent Assistant 🤖</h1>
                <h3>powered by Azure AI + Fabric </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Chat interface
        user_input = st.chat_input("What do you want to know about...")
        chat_container = st.container(height=500)

        with chat_container:
            render_chat_history(chat_container)
            
            if user_input:
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "role": "user", 
                    "content": user_input, 
                    "avatar": "🧑‍💻"
                })
                
                # Display user message
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(user_input, unsafe_allow_html=True)
                
                # First, show the routing analysis
                with st.status("🧠 Analyzing query and routing to optimal agent...", expanded=True) as status:
                    # Get routing decision first
                    routing_decision = get_agent_routing_decision(user_input)
                    
                    # Show decision tree logic
                    st.write("**Decision Tree Analysis:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        fabric_active = routing_decision["agent"] == "unified_fabric"
                        st.markdown(f"{'🟢' if fabric_active else '⚪'} **📊 Structured Data**")
                        if fabric_active:
                            st.success("✅ Selected - Best fit for query")
                        else:
                            st.write("❌ Not selected")
                    
                    with col2:
                        foundry_active = routing_decision["agent"] == "foundry"  
                        st.markdown(f"{'🟢' if foundry_active else '⚪'} **📁 Documents**")
                        if foundry_active:
                            st.success("✅ Selected - Best fit for query")
                        else:
                            st.write("❌ Not selected")
                    
                    with col3:
                        copilot_active = routing_decision["agent"] == "copilot"
                        st.markdown(f"{'🟢' if copilot_active else '⚪'} **🌐 Real-time**")
                        if copilot_active:
                            st.success("✅ Selected - Best fit for query")
                        else:
                            st.write("❌ Not selected")
                    
                    st.write(f"**🎯 Final Decision**: {routing_decision['icon']} {routing_decision['name']}")
                    st.write(f"**Purpose**: {routing_decision['purpose']}")
                    
                    status.update(label=f"✅ Agent selected: {routing_decision['name']}", state="complete")
                
                # Now process with the selected agent
                with st.spinner(f"Processing with {routing_decision['name']}..."):
                    try:
                        # Use production agent system from notebook 06
                        result, _ = asyncio.run(production_agent_system(user_input))
                        
                        # Create agent selection summary for chat history
                        agent_selection_msg = f"""
**{routing_decision['icon']} Agent Used: {routing_decision['name']}**
- **Purpose**: {routing_decision['purpose']}  
- **Reasoning**: {routing_decision['reasoning']}
- **Data Sources**: {routing_decision['data_sources']}
                        """
                        
                        # Add agent selection info to chat history
                        st.session_state.chat_history.append({
                            "role": "info",
                            "content": agent_selection_msg.strip(),
                            "avatar": "🎯"
                        })
                        
                        # Add assistant response to chat history  
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result,
                            "avatar": "🤖"
                        })
                        
                        # Display assistant message
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(result, unsafe_allow_html=True)
                            
                    except Exception as e:
                        error_msg = f"Error processing request: {str(e)}"
                        logger.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg,
                            "avatar": "❌"
                        })
                        
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
