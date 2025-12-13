"""A2A server entry point for Jeff's scheduling agent."""

from __future__ import annotations

import argparse
import os

import uvicorn
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import JeffAgent
from agent_executor import JeffAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

DEFAULT_HOST = os.getenv("JEFF_AGENT_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("JEFF_AGENT_PORT", "10004"))


def build_agent_card(host: str, port: int) -> AgentCard:
    skill = AgentSkill(
        id="schedule_badminton",
        name="Jeff Availability Lookup",
        description="Returns Jeff's availability for badminton scheduling requests.",
        tags=["scheduling", "badminton"],
        examples=["Are you free to play badminton on 2026-03-01?"],
    )

    return AgentCard(
        name="Jeff's Agent",
        description="Participant scheduling agent for Jeff.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=JeffAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=JeffAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(),
        skills=[skill],
    )


def build_application(host: str, port: int) -> A2AStarletteApplication:
    request_handler = DefaultRequestHandler(
        agent_executor=JeffAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=build_agent_card(host, port),
        http_handler=request_handler,
    )


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    application = build_application(host, port)
    uvicorn.run(application.build(), host=host, port=port)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Jeff's A2A scheduling agent server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind.")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port for the A2A HTTP server.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(host=args.host, port=args.port)
