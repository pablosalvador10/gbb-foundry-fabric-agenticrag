"""
Realtime Assistant Agent Setup and Usage Examples

USAGE PATTERN:
1. Run create_agent() ONCE offline to create agent and upload files
2. Use the returned agent_id in your .env file
3. In production, setup_realtime_assistant() will connect to existing agent automatically
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Load environment variables
try:
    import dotenv
    dotenv.load_dotenv(".env", override=True)
    print("Environment variables loaded from .env file")
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables")

from app.agent_registry.RealtimeAssistant.main import (
    create_realtime_assistant,
    setup_realtime_assistant,
)


async def create_agent():
    """
    OFFLINE SETUP: Run this ONCE to create the agent.
    
    Creates:
    - Uploads airport_operations.pdf
    - Creates vector store
    - Creates Azure AI agent with all tools
    - Returns IDs to save in .env
    
    Returns:
        Tuple of (agent, agent_id, vector_store_id, file_id)
    """
    print("=" * 80)
    print("CREATING REALTIME ASSISTANT AGENT")
    print("=" * 80)
    
    agent, agent_id, vector_store_id, file_id = await create_realtime_assistant()
    
    print("\n" + "=" * 80)
    print("SUCCESS - Agent created")
    print("=" * 80)
    print(f"\nAgent ID: {agent_id}")
    print(f"Vector Store ID: {vector_store_id}")
    print(f"File ID: {file_id}")
    print("\n" + "=" * 80)
    print("ADD THESE TO YOUR .env FILE:")
    print("=" * 80)
    print(f"REALTIME_ASSISTANT_AGENT_ID={agent_id}")
    print(f"FILE_SEARCH_VECTOR_STORE_ID={vector_store_id}")
    print(f"AIRLINE_OPS_FILE_ID={file_id}")
    print("=" * 80)
    
    return agent, agent_id, vector_store_id, file_id


async def test_agent(agent_id: str):
    """
    Test the agent with sample queries.
    
    Args:
        agent_id: The Azure AI agent ID
    """
    print("\n" + "=" * 80)
    print("TESTING AGENT")
    print("=" * 80)
    
    agent = await setup_realtime_assistant(agent_id=agent_id)
    
    test_queries = [
        "What's the weather in New York?",
        "What time is it in UTC?",
        "Search for recent airport delays news",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        result = await agent.run(query)
        print(f"Response: {result.text}")
        print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


async def main():
    """
    Main entry point.
    
    Uncomment the appropriate function based on what you need:
    - create_agent(): First-time setup (run once offline)
    - test_agent(): Test existing agent (requires agent_id in .env)
    """
    
    print("\n" + "=" * 80)
    print("PREREQUISITES CHECK")
    print("=" * 80)
    print("\n1. Azure CLI Authentication:")
    print("   Run: az login")
    print("   Verify: az account show")
    print("\n2. Required Azure Permissions:")
    print("   Your account needs these roles on the Azure AI project:")
    print("   - Azure AI Developer (or Contributor)")
    print("   - Storage Blob Data Contributor")
    print("\n3. Environment Variables:")
    print("   Ensure .env file has:")
    print("   - AZURE_AI_PROJECT_ENDPOINT")
    print("   - REALTIME_ASSISTANT_CONFIG")
    print("=" * 80)
    
    # OPTION 1: Create new agent (run once offline)
    # Uncomment to create agent:
    try:
        agent, agent_id, vector_store_id, file_id = await create_agent()
    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR - TROUBLESHOOTING GUIDE")
        print("=" * 80)
        print("\nIf you see 'File storage access permission error':")
        print("\n1. Verify Azure CLI login:")
        print("   az login --use-device-code")
        print("   az account show")
        print("\n2. Check your Azure AI project permissions:")
        print("   Go to Azure Portal > Your AI Project > Access Control (IAM)")
        print("   Ensure you have 'Azure AI Developer' or 'Contributor' role")
        print("\n3. Check storage account permissions:")
        print("   Your AI project uses a storage account for files")
        print("   Ensure you have 'Storage Blob Data Contributor' role")
        print("\n4. Alternative: Use Azure AI Studio to upload files manually")
        print("   Then use setup_realtime_assistant() with existing agent_id")
        print("=" * 80)
        raise
    
    # OPTION 2: Test existing agent (requires agent_id)
    # Uncomment and set agent_id to test:
    # agent_id = "YOUR_AGENT_ID_HERE"
    # await test_agent(agent_id)


if __name__ == "__main__":
    asyncio.run(main())
