"""
Intelligent Agent Orchestrator
Uses Azure OpenAI to make semantic routing decisions between agents.
"""

import asyncio
from typing import Annotated, Tuple, Dict, Any
from pydantic import Field

from agent_framework import ChatAgent, AgentThread
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.settings import AZURE_OPENAI_API_ENDPOINT, AZURE_OPENAI_KEY, AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID
from utils.ml_logging import get_logger

logger = get_logger()


class IntelligentOrchestrator:
    """
    Intelligent orchestrator that uses Azure OpenAI to make semantic routing decisions.
    
    This orchestrator analyzes user queries semantically and routes them to the most
    appropriate specialized agent based on intent and context rather than simple keywords.
    """
    
    def __init__(self):
        self.routing_agent = None
        self.foundry_agent = None
        self.fabric_agent = None
        self._setup_routing_agent()
    
    def _setup_routing_agent(self) -> None:
        """Initialize the routing decision agent."""
        try:
            # Create the routing agent with semantic understanding
            self.routing_agent = ChatAgent(
                chat_client=AzureOpenAIChatClient(
                    endpoint=AZURE_OPENAI_API_ENDPOINT,
                    api_key=AZURE_OPENAI_KEY,
                    deployment_name=AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID,
                    credential=AzureCliCredential()
                ),
                name="IntelligentRouter",
                instructions="""You are an intelligent routing agent that analyzes user queries and determines which specialized agent should handle the request.

AGENT OPTIONS:
1. **foundry_agent** - Use for FedEx Electronic Trade Documents (ETD) queries:
   - Document management, upload procedures, letterheads, signatures
   - International shipping documentation, customs forms, commercial invoices
   - Trade compliance, NAFTA certificates, certificates of origin
   - ETD system configuration, troubleshooting, best practices

2. **fabric_agent** - Use for structured data analysis and airline/airport information:
   - Product catalogs, sales analytics, revenue data, KPIs, metrics
   - Airport operations, flight information, delays, routes, aircraft data
   - Airline information, crew data, baggage systems, terminal operations
   - Any analytical queries about structured datasets

ROUTING DECISION PROCESS:
1. Analyze the user's query semantically
2. Determine the primary intent and domain
3. Consider if the query needs:
   - Document management/trade procedures → foundry_agent
   - Data analysis/airline operations → fabric_agent

RESPONSE FORMAT:
Respond with ONLY the agent name: either "foundry_agent" or "fabric_agent"

Examples:
- "How do I upload my company letterhead for commercial invoices?" → foundry_agent
- "What are the routes with the biggest delays?" → fabric_agent  
- "Help me with ETD configuration" → foundry_agent
- "Show me airport analytics" → fabric_agent
- "What documents do I need for international shipping?" → foundry_agent
- "Which airlines have the most flights?" → fabric_agent""",
                tools=[]
            )
            logger.info("✅ Created intelligent routing agent")
            
        except Exception as e:
            logger.error(f"❌ Failed to create routing agent: {e}")
            self.routing_agent = None

    async def route_query(self, query: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Intelligently route a user query to the appropriate agent.
        
        Args:
            query: The user's question or request
            
        Returns:
            Tuple of (agent_name, reasoning, routing_info)
        """
        if not self.routing_agent:
            return "fabric_agent", "Routing agent not available, defaulting to fabric agent", {
                "agent": "fabric_agent",
                "name": "Fabric Data Agent", 
                "icon": "📊",
                "purpose": "Structured Data Analytics (Default)",
                "reasoning": "Routing agent unavailable",
                "confidence": "low"
            }
        
        try:
            # Get routing decision from the intelligent agent
            routing_prompt = f"""
            Analyze this user query and determine which agent should handle it:
            
            Query: "{query}"
            
            Respond with ONLY the agent name: foundry_agent or fabric_agent
            """
            
            result = await self.routing_agent.run(routing_prompt)
            selected_agent = result.text.strip().lower()
            
            # Validate and normalize the response
            if "foundry" in selected_agent:
                agent_name = "foundry_agent"
                routing_info = {
                    "agent": "foundry",
                    "name": "FedEx ETD Agent",
                    "icon": "📦", 
                    "purpose": "FedEx Electronic Trade Documents Expert",
                    "reasoning": "AI routing detected FedEx ETD or trade documentation intent",
                    "confidence": "high"
                }
            else:  # Default to fabric for any other case
                agent_name = "fabric_agent"
                routing_info = {
                    "agent": "unified_fabric",
                    "name": "Fabric Data Agent",
                    "icon": "📊",
                    "purpose": "Structured Data Analytics & Airport Information", 
                    "reasoning": "AI routing detected structured data or airline/airport information intent",
                    "confidence": "high"
                }
            
            logger.info(f"🤖 Intelligent routing: {query[:50]}... → {agent_name}")
            return agent_name, f"Semantic analysis routed to {routing_info['name']}", routing_info
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent routing: {e}")
            # Fallback to fabric agent
            return "fabric_agent", f"Routing error, defaulting to fabric agent: {str(e)}", {
                "agent": "unified_fabric", 
                "name": "Fabric Data Agent",
                "icon": "📊",
                "purpose": "Structured Data Analytics (Fallback)",
                "reasoning": "Error in routing decision",
                "confidence": "low"
            }

    def set_agents(self, foundry_agent: Any, fabric_agent: Any) -> None:
        """
        Set the specialized agents that this orchestrator can route to.
        
        Args:
            foundry_agent: The FedEx ETD foundry agent
            fabric_agent: The unified fabric agent with data tools
        """
        self.foundry_agent = foundry_agent
        self.fabric_agent = fabric_agent
        logger.info("✅ Specialized agents registered with orchestrator")

    async def execute_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Route and execute a query using the appropriate specialized agent.
        
        Args:
            query: The user's question or request
            
        Returns:
            Tuple of (response_text, routing_info)
        """
        # Get routing decision
        agent_name, reasoning, routing_info = await self.route_query(query)
        
        try:
            # Execute with the selected agent
            if agent_name == "foundry_agent" and self.foundry_agent:
                result = await self.foundry_agent.run(query)
                response_text = result.text if hasattr(result, 'text') else str(result)
            elif agent_name == "fabric_agent" and self.fabric_agent:
                result = await self.fabric_agent.run(query)
                response_text = result.text if hasattr(result, 'text') else str(result)
            else:
                response_text = f"❌ Selected agent ({agent_name}) not available"
                
            return response_text, routing_info
            
        except Exception as e:
            logger.error(f"❌ Error executing query with {agent_name}: {e}")
            return f"❌ Error processing query: {str(e)}", routing_info


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> IntelligentOrchestrator:
    """Get the global orchestrator instance, creating it if needed."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IntelligentOrchestrator()
    return _orchestrator


async def intelligent_agent_routing(query: str, foundry_agent: Any, fabric_agent: Any) -> Tuple[str, Dict[str, Any]]:
    """
    Convenience function for intelligent agent routing.
    
    Args:
        query: User's question
        foundry_agent: FedEx ETD agent
        fabric_agent: Unified fabric agent with data tools
        
    Returns:
        Tuple of (response, routing_info)
    """
    orchestrator = get_orchestrator()
    orchestrator.set_agents(foundry_agent, fabric_agent)
    return await orchestrator.execute_query(query)