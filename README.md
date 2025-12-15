# A2A Badminton Scheduling System

## Overview

This project demonstrates a multi-agent scheduling workflow using the Agent-to-Agent (A2A) protocol. A host coordinator agent communicates with two participant agents, collects availability information, identifies a feasible time, and books a badminton court through local tools.

The project is intentionally built with multiple agent frameworks to demonstrate protocol-level interoperability:

- Host coordinator: Google ADK
- Participant agent (Jeff): LangChain + LangGraph
- Participant agent (Mark): CrewAI

## Problem Statement

Scheduling a simple group activity becomes harder when availability information is distributed across different assistants, systems, or services. In a real organization, each participant may have a separate agent with its own framework, tools, and runtime.

This project addresses the following engineering problem:

- How can independent agents, implemented in different frameworks, collaborate over a shared protocol to complete a scheduling task end-to-end?

The system demonstrates:

- Agent-to-agent communication over HTTP (A2A)
- Cross-framework interoperability
- Tool-augmented decision making (availability lookup and court booking)
- A coordinator pattern for multi-agent orchestration

## System Design

### Components

| Component | Framework | Responsibility | Default Port |
| --- | --- | --- | --- |
| Elon Agent | Google ADK | Coordinator / orchestrator | 8000 (ADK web UI) |
| Jeff Agent | LangChain + LangGraph | Participant availability agent | 10004 |
| Mark Agent | CrewAI | Participant availability agent | 10005 |

### Coordination Flow

1. User asks the host coordinator to organize a badminton game.
2. Host agent sends A2A requests to participant agents.
3. Participant agents query their local availability tools.
4. Host agent compares responses to find a workable slot.
5. Host agent checks local court availability.
6. Host agent books a court and returns the result.

## Repository Structure

```text
a2a-project/
├── README.md
├── .env.example
├── elon_agent/                 # Host coordinator (Google ADK)
│   ├── pyproject.toml
│   ├── uv.lock
│   └── elon/
│       ├── __init__.py
│       ├── agent.py            # ADK host agent + A2A client integration
│       └── tools.py            # Court schedule and booking tools
├── jeff_agent/                 # Participant agent (LangChain/LangGraph)
│   ├── __main__.py             # A2A server entry point
│   ├── agent.py                # LangChain agent logic
│   ├── agent_executor.py       # A2A executor wrapper
│   ├── tools.py                # Demo availability tool
│   ├── pyproject.toml
│   └── uv.lock
├── mark_agent/                 # Participant agent (CrewAI)
│   ├── __main__.py             # A2A server entry point
│   ├── agent.py                # CrewAI agent logic
│   ├── agent_executor.py       # A2A executor wrapper
│   ├── tools.py                # Demo availability tool + CrewAI tool adapter
│   ├── pyproject.toml
│   └── uv.lock
└── tests/
    └── test_tool_contracts.py  # Unit tests for local scheduling tools
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key for Gemini models

## Configuration

Create a `.env` file at the repository root:

```bash
cp .env.example .env
```

Set the required value:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

Optional host configuration:

- `A2A_REMOTE_AGENT_URLS` (comma-separated participant agent URLs)
  - Default: `http://localhost:10004,http://localhost:10005`

## Installation

Each agent is an independent Python project with its own dependencies.

```bash
cd elon_agent
uv sync

cd ../jeff_agent
uv sync

cd ../mark_agent
uv sync
```

## Running the System

Start the participant agents first, then the host coordinator.

### 1. Start Jeff Agent (Port 10004)

```bash
cd jeff_agent
uv run python __main__.py
```

### 2. Start Mark Agent (Port 10005)

```bash
cd mark_agent
uv run python __main__.py
```

### 3. Start Elon Agent (ADK Web UI)

```bash
cd elon_agent
uv run adk web
```

ADK typically serves the local UI at:

```text
http://127.0.0.1:8000
```

## Verifying the Services

Use these endpoints to confirm the servers are running:

```bash
# Participant agent cards
curl http://localhost:10004/.well-known/agent-card.json
curl http://localhost:10005/.well-known/agent-card.json

# ADK app list (host agent UI backend)
curl http://127.0.0.1:8000/list-apps
```

## Example User Requests

Use the host agent UI and try prompts such as:

- `Organize a badminton game with Jeff and Mark next week.`
- `Ask Jeff and Mark for availability and find a common time.`
- `Check court availability for the agreed date and book a slot.`

Note: demo availability and court schedules are generated relative to the current date at runtime, so exact dates vary per run.

## Development Notes

### Testing

Run the unit tests for local scheduling tools:

```bash
python3 -m unittest discover -s tests
```

### Code Quality Improvements Included

This repository has been refactored to improve maintainability and reliability:

- Consistent typing and module structure across agents
- Clearer separation of responsibilities (agent logic vs A2A executor vs tools)
- Better input validation for dates and times
- Reduced blocking behavior in async handlers by using worker threads for sync framework calls
- More resilient host startup when participant agents are temporarily unavailable
- Removal of placeholder/stub entry files

## Limitations

This is a demonstration system and intentionally uses in-memory data:

- Participant calendars are simulated (not backed by real calendar providers)
- Court booking uses an in-memory schedule (no persistence)
- No authentication or authorization on A2A endpoints
- Coordination logic depends on LLM reasoning quality and prompt adherence

## Extension Ideas

Potential next steps for production-style evolution:

1. Replace fake availability tools with Google Calendar / Outlook integrations.
2. Add persistent storage for bookings and request history.
3. Add structured response parsing and explicit time-slot intersection logic in the host agent.
4. Add CI (linting, tests, static checks) and integration tests.
5. Add authentication and service discovery for A2A endpoints.

## License

This project is provided for educational and portfolio purposes.
