# Multi-Agent Architecture - Airline Operations Assistant

## 🎯 Architecture Overview

This system uses a **hierarchical agent architecture** where a main orchestrator delegates work to specialized sub-agents using the `.as_tool()` pattern.

```
┌─────────────────────────────────────────────┐
│   AirlineIntelligentAssistant (Main)        │
│   - Entry point for all user queries        │
│   - Coordinates between sub-agents          │
│   - Azure OpenAI based                      │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────────────┐
│AirlineOps    │  │RealtimeAssistant     │
│Context       │  │(Azure Foundry)       │
│              │  │                      │
│- Fabric Data │  │- Bing Search         │
│- Flights     │  │- File Search         │
│- Baggage     │  │- Weather (Function)  │
│- Routes      │  │- Time (Function)     │
│- Airports    │  │                      │
│- SLA Metrics │  │                      │
└──────────────┘  └──────────────────────┘
```

## 📁 Project Structure

```
app/agent_registry/
├── AirlineIntelligentAssistant/    # Main orchestrator
│   ├── __init__.py
│   ├── conf.yaml                   # Main agent config
│   └── main.py                     # Creates agent with sub-agents as tools
│
├── AirlineOpsContext/              # Operational data sub-agent
│   ├── __init__.py
│   ├── conf.yaml                   # Config with Fabric endpoints
│   └── main.py                     # Azure OpenAI + Fabric retrieval
│
└── RealtimeAssistant/              # Realtime capabilities sub-agent
    ├── __init__.py
    ├── conf.yaml                   # Config for Foundry agent
    ├── main.py                     # Azure Foundry agent setup
    └── tools.py                    # Custom functions (weather, time)
```

## 🔧 Agent Details

### 1. AirlineIntelligentAssistant (Main Orchestrator)

**Type**: Azure OpenAI Agent  
**Role**: Entry point and coordinator  
**Location**: `app/agent_registry/AirlineIntelligentAssistant/`

**Capabilities**:
- Receives all user queries
- Automatically routes to appropriate sub-agent
- Can call multiple sub-agents if needed
- Synthesizes responses

**Configuration**:
```yaml
name: "AirlineIntelligentAssistant"
azure_openai:
  endpoint: "${AZURE_OPENAI_API_ENDPOINT}"
  api_key: "${AZURE_OPENAI_API_KEY}"
  deployment: "${AZURE_OPENAI_DEPLOYMENT_NAME}"
```

**Usage**:
```python
from app.agent_registry.AirlineIntelligentAssistant.main import setup_airline_intelligent_assistant

agent = await setup_airline_intelligent_assistant()
result = await agent.run("What flights are delayed at ORD?")
```

### 2. AirlineOpsContext (Operational Data)

**Type**: Azure OpenAI Agent with Fabric Integration  
**Role**: Retrieve operational data from Microsoft Fabric  
**Location**: `app/agent_registry/AirlineOpsContext/`

**Capabilities**:
- Flight schedules, delays, cancellations
- Baggage tracking and performance
- Route information
- Airport operations
- SLA metrics

**Tool**: `retrieve_operational_context(query)`  
**Exposed as**: `AirlineOpsContext` tool to main agent

**Configuration**:
```yaml
name: "AirlineOpsContext"
azure_openai: { ... }
fabric_endpoints:
  airport_info: "${FABRIC_AIRPORT_INFO_ENDPOINT}"
tools:
  - retrieve_operational_context
```

### 3. RealtimeAssistant (Realtime Capabilities)

**Type**: Azure AI Foundry Agent  
**Role**: Provide realtime information and search  
**Location**: `app/agent_registry/RealtimeAssistant/`

**Capabilities**:
- **Bing Grounding Search**: Current events, web search
- **File Search**: Document retrieval from vector stores
- **Weather**: Get weather for any location (function tool)
- **Time**: Get current UTC time (function tool)

**Tools**: 
- `HostedWebSearchTool` (Bing)
- `HostedFileSearchTool` (Documents)
- `get_weather(location)` (Function)
- `get_time()` (Function)

**Exposed as**: `RealtimeAssistant` tool to main agent

**Configuration**:
```yaml
name: "RealtimeAssistant"
azure_ai_foundry:
  endpoint: "${AZURE_AI_PROJECT_ENDPOINT}"
  model_deployment: "${AZURE_AI_MODEL_DEPLOYMENT_NAME}"
  agent_id: "${REALTIME_ASSISTANT_AGENT_ID}"  # Optional - reuse existing
bing_search:
  enabled: true
  connection_id: "${BING_CONNECTION_ID}"
file_search:
  enabled: true
  vector_store_id: "${FILE_SEARCH_VECTOR_STORE_ID}"
tools:
  - get_weather
  - get_time
```

## 🔄 How It Works: The .as_tool() Pattern

The main orchestrator uses the `.as_tool()` pattern to convert sub-agents into callable tools:

```python
# 1. Initialize sub-agents
ops_context_agent = airline_ops_context_agent  # Already created
realtime_agent = await setup_realtime_assistant()

# 2. Convert to tools
ops_tool = ops_context_agent.as_tool(
    name="AirlineOpsContext",
    description="Query operational data from Microsoft Fabric...",
    arg_name="query",
    arg_description="The operational question..."
)

realtime_tool = realtime_agent.as_tool(
    name="RealtimeAssistant",
    description="Access real-time information...",
    arg_name="query",
    arg_description="The query for web search, weather..."
)

# 3. Create main agent with sub-agents as tools
main_agent = AzureOpenAIChatClient(credential=credential).create_agent(
    name="AirlineIntelligentAssistant",
    instructions=instructions,
    tools=[ops_tool, realtime_tool]
)
```

## 🚀 Query Flow Example

**User Query**: "What's the weather in New York and are there any delays at JFK?"

1. **User** → `AirlineIntelligentAssistant`
2. **Main Agent** analyzes query and determines:
   - Weather query → needs `RealtimeAssistant`
   - Delays query → needs `AirlineOpsContext`
3. **Main Agent** calls both sub-agents:
   - `RealtimeAssistant.get_weather("New York")`
   - `AirlineOpsContext.retrieve_operational_context("delays at JFK")`
4. **Main Agent** synthesizes responses
5. **User** receives comprehensive answer

## 🔑 Environment Variables Required

```bash
# Main Orchestrator
AIRLINE_INTELLIGENT_ASSISTANT_CONFIG=./app/agent_registry/AirlineIntelligentAssistant/conf.yaml
AZURE_OPENAI_API_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Operational Data Agent
AIRLINE_OPS_CONTEXT_CONFIG=./app/agent_registry/AirlineOpsContext/conf.yaml
FABRIC_AIRPORT_INFO_ENDPOINT=https://...

# Realtime Assistant (Foundry)
REALTIME_ASSISTANT_CONFIG=./app/agent_registry/RealtimeAssistant/conf.yaml
AZURE_AI_PROJECT_ENDPOINT=https://...
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4
BING_CONNECTION_ID=your-bing-connection-id
REALTIME_ASSISTANT_AGENT_ID=asst_... # Optional - for reuse
FILE_SEARCH_VECTOR_STORE_ID=vs_...  # Optional
```

## ✨ Key Benefits

1. **Automatic Routing**: Framework handles delegation, no manual routing logic needed
2. **Composable**: Easy to add new sub-agents as tools
3. **Clean Separation**: Each agent has clear responsibilities
4. **Reusable**: Sub-agents work independently or as tools
5. **Scalable**: Add more capabilities by adding more sub-agents
6. **Dynamic Configuration**: All agents configured via YAML
7. **Agent Persistence**: Foundry agents can be reused via agent_id

## 🔧 Adding New Sub-Agents

To add a new sub-agent:

1. Create directory: `app/agent_registry/YourAgent/`
2. Add `conf.yaml` with configuration
3. Add `main.py` with setup function returning `ChatAgent`
4. In main orchestrator, import and convert to tool:
   ```python
   new_agent = await setup_your_agent()
   new_tool = new_agent.as_tool(name="YourAgent", description="...")
   # Add to tools list
   ```

## 📝 Migration Notes

**Old Pattern**: Manual routing with keyword scoring  
**New Pattern**: Automatic delegation via `.as_tool()`

**Removed**:
- `IntelligentOrchestrator` with manual routing logic
- `route_query()` function with keyword scoring
- Complex routing decisions in code

**Added**:
- `AirlineIntelligentAssistant` main orchestrator
- `.as_tool()` pattern for sub-agent integration
- Framework-handled automatic routing
