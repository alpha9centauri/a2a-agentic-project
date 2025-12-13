"""LangChain/LangGraph implementation of Jeff's participant agent."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages.ai import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver

from tools import get_availability

load_dotenv()

_MEMORY = MemorySaver()


class JeffAgent:
    """Participant agent that answers questions about Jeff's availability."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self) -> None:
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment")

        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.system_prompt = (
            "You are Jeff Bezos's scheduling assistant.\n"
            "Your job is to answer questions about Jeff's badminton availability.\n"
            "Always use the get_availability tool for date-specific scheduling requests.\n"
            "If a request is unrelated to scheduling, respond politely that you can only help "
            "with badminton scheduling."
        )
        self.graph = create_agent(
            self.model,
            tools=[get_availability],
            system_prompt=self.system_prompt,
            checkpointer=_MEMORY,
        )

    async def get_response(self, query: str, context_id: str | int) -> str:
        """Return the latest AI response content as plain text."""
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": str(context_id)}}

        # LangGraph invoke is synchronous in this usage; run it in a worker thread so
        # the A2A server event loop remains responsive.
        raw_response = await asyncio.to_thread(self.graph.invoke, inputs, config)
        return self._extract_latest_ai_text(raw_response)

    @staticmethod
    def _extract_latest_ai_text(raw_response: dict[str, Any]) -> str:
        messages = raw_response.get("messages", [])
        ai_contents = [
            message.content for message in messages if isinstance(message, AIMessage)
        ]
        if not ai_contents:
            return "No response generated."
        return JeffAgent._normalize_content(ai_contents[-1]) or "No response generated."

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    text_parts.append(str(part.get("text", "")).strip())
                else:
                    text_parts.append(str(part).strip())
            return " ".join(part for part in text_parts if part)

        return str(content).strip()
