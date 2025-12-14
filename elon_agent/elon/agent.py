"""Host coordinator agent implemented with Google ADK and A2A clients."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import uuid
from typing import Any, Iterable

import httpx
import nest_asyncio
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.tool_context import ToolContext

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)

from .tools import book_badminton_court, list_court_availabilities

load_dotenv()
nest_asyncio.apply()

LOGGER = logging.getLogger(__name__)

DEFAULT_REMOTE_AGENT_URLS = ("http://localhost:10004", "http://localhost:10005")
REMOTE_AGENT_URLS_ENV_VAR = "A2A_REMOTE_AGENT_URLS"
REMOTE_AGENT_TIMEOUT_SECONDS = 10


class RemoteAgentConnection:
    """Wraps a persistent A2A client connection to one participant agent."""

    def __init__(self, agent_card: AgentCard, agent_url: str) -> None:
        self.agent_card = agent_card
        self.agent_url = agent_url.rstrip("/")
        self.http_client = httpx.AsyncClient(timeout=REMOTE_AGENT_TIMEOUT_SECONDS)
        self.client = A2AClient(self.http_client, agent_card, url=self.agent_url)

    async def send_message(
        self, message_request: SendMessageRequest
    ) -> SendMessageResponse:
        return await self.client.send_message(message_request)


class ElonAgent:
    """Coordinates scheduling by calling participant A2A agents and local tools."""

    def __init__(self, remote_agent_urls: Iterable[str] | None = None) -> None:
        self.remote_agent_urls = [url.rstrip("/") for url in (remote_agent_urls or []) if url]
        self.remote_connections: dict[str, RemoteAgentConnection] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agent: Agent | None = None

    async def create_agent(self) -> Agent:
        await self._load_remote_agents()

        self.agent = Agent(
            model="gemini-2.0-flash",
            name="elon_agent",
            description=(
                "Coordinates badminton scheduling by querying participant agents "
                "and booking a court."
            ),
            instruction=self._build_instruction(),
            tools=[
                self.send_message,
                book_badminton_court,
                list_court_availabilities,
            ],
        )
        return self.agent

    def _build_instruction(self) -> str:
        friend_names = sorted(self.cards.keys())
        friends_section = "\n".join(f"- {name}" for name in friend_names)
        if not friends_section:
            friends_section = "- No participant agents are currently connected. Ask the user to start them."

        return (
            "You are the host coordinator for badminton scheduling.\n"
            "Your responsibilities are:\n"
            "1. Ask participant agents for availability (starting from tomorrow).\n"
            "2. Find a common timeslot.\n"
            "3. Check court availability with local tools.\n"
            "4. Book the court after confirmation.\n\n"
            f"Connected participant agents:\n{friends_section}\n\n"
            f"Today's date: {dt.date.today().isoformat()}\n"
            "Use ISO date format (YYYY-MM-DD) when calling tools and remote agents."
        )

    async def _load_remote_agents(self) -> None:
        if not self.remote_agent_urls:
            LOGGER.warning("No remote agent URLs configured for the host agent.")
            return

        async with httpx.AsyncClient(timeout=REMOTE_AGENT_TIMEOUT_SECONDS) as client:
            for url in self.remote_agent_urls:
                resolver = A2ACardResolver(client, url)
                try:
                    card = await resolver.get_agent_card()
                except Exception as exc:  # noqa: BLE001 - best-effort startup
                    LOGGER.warning("Failed to load agent card from %s: %s", url, exc)
                    continue

                self.remote_connections[card.name] = RemoteAgentConnection(card, url)
                self.cards[card.name] = card

        if not self.cards:
            LOGGER.warning(
                "Host agent started without connected participant agents. "
                "Remote messaging will fail until participants are available."
            )

    def _get_remote_connection(self, agent_name: str) -> RemoteAgentConnection | None:
        exact_match = self.remote_connections.get(agent_name)
        if exact_match:
            return exact_match

        normalized = agent_name.casefold()
        for name, connection in self.remote_connections.items():
            if name.casefold() == normalized:
                return connection
        return None

    async def send_message(
        self, agent_name: str, task: str, _tool_context: ToolContext
    ) -> dict[str, Any]:
        """Send a message to a participant agent via the A2A protocol."""
        connection = self._get_remote_connection(agent_name)
        if connection is None:
            available_agents = sorted(self.remote_connections.keys())
            raise ValueError(
                f"Unknown agent '{agent_name}'. Available agents: {available_agents or 'none'}"
            )

        message_id = str(uuid.uuid4())
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
            }
        }

        request = SendMessageRequest(
            id=message_id,
            params=MessageSendParams.model_validate(payload),
        )
        response = await connection.send_message(request)

        response_payload = (
            response.model_dump(mode="json")
            if hasattr(response, "model_dump")
            else str(response)
        )
        return {
            "status": "success",
            "agent_name": connection.agent_card.name,
            "agent_url": connection.agent_url,
            "response": response_payload,
        }


def _configured_remote_agent_urls() -> list[str]:
    raw_value = os.getenv(REMOTE_AGENT_URLS_ENV_VAR, "")
    if not raw_value.strip():
        return list(DEFAULT_REMOTE_AGENT_URLS)
    return [url.strip() for url in raw_value.split(",") if url.strip()]


async def setup() -> Agent:
    host = ElonAgent(remote_agent_urls=_configured_remote_agent_urls())
    return await host.create_agent()


root_agent = asyncio.run(setup())
