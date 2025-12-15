# Airline Ops Assistant - How the Agents Work

## Overview

This uses a hierarchical pattern: one main agent delegates to specialized sub-agents using `.as_tool()`.

```
┌─────────────────────────────────────────────┐
│   AirlineIntelligentAssistant (Orchestrator)│
│   - Routes queries to the right sub-agent   │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐  ┌──────────────────────┐
│AirlineOps    │  │RealtimeAssistant     │
│Context       │  │(Foundry)             │
│              │  │                      │
│- Fabric Data │  │- Bing Search         │
│- Flights     │  │- File Search         │
│- Baggage     │  │- Weather             │
│- Routes      │  │- Time                │
└──────────────┘  └──────────────────────┘
```

## Files

```
app/agent_registry/
├── AirlineIntelligentAssistant/
│   ├── conf.yaml      # Config
│   └── main.py        # Setup with sub-agents as tools
│
├── AirlineOpsContext/
│   ├── conf.yaml      # Fabric endpoint config
│   └── main.py        # Queries Fabric
│
└── RealtimeAssistant/
    ├── conf.yaml      # Foundry config
    ├── create_agent.py # Run once to create the agent
    ├── main.py        # Agent setup
    └── tools.py       # Weather, time functions
```

## The Agents

**AirlineIntelligentAssistant** - Main orchestrator (Azure OpenAI). Figures out which sub-agent to call.

**AirlineOpsContext** - Queries Microsoft Fabric for operational data (flights, baggage, routes, SLAs).

**RealtimeAssistant** - Azure AI Foundry agent with Bing search, file search, weather, and time tools.

## The `.as_tool()` Pattern

You can turn any agent into a tool for another agent:

```python
ops_agent = await setup_airline_ops_context_agent()
realtime_agent = await setup_realtime_assistant()

# Convert to tools
ops_tool = ops_agent.as_tool(
    name="AirlineOpsContext",
    description="Query Fabric for operational data",
    arg_name="query"
)

realtime_tool = realtime_agent.as_tool(
    name="RealtimeAssistant", 
    description="Web search, weather, time",
    arg_name="query"
)

# Main agent uses them as tools
orchestrator = ChatAgent(
    name="AirlineIntelligentAssistant",
    tools=[ops_tool, realtime_tool]
)
```

## Example Flow

**User**: "What's the weather in NYC and any delays at JFK?"

1. Query hits `AirlineIntelligentAssistant`
2. Orchestrator decides it needs both sub-agents
3. Calls `RealtimeAssistant` for weather
4. Calls `AirlineOpsContext` for delays
5. Combines responses and returns

## Env Vars

Check `.env.example`. The key ones:

```bash
# Azure OpenAI
AZURE_OPENAI_API_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Foundry
AZURE_AI_PROJECT_ENDPOINT=https://...
BING_CONNECTION_ID=your-bing-connection-id

# Fabric
FABRIC_CONNECTION_NAME=your-fabric-connection
```

## Adding a New Agent

1. Create `app/agent_registry/YourAgent/`
2. Add `conf.yaml` and `main.py`
3. Return a `ChatAgent` from your setup function
4. Add it as a tool in the orchestrator
