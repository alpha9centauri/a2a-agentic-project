"""CrewAI implementation of Mark's participant agent."""

from __future__ import annotations

import asyncio
import os

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

from tools import AvailabilityTool

load_dotenv()


class MarkAgent:
    """Participant agent that answers questions about Mark's availability."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        self.llm = LLM(
            model="gemini/gemini-2.0-flash",
            api_key=api_key,
        )
        self.agent = Agent(
            role="Scheduling Assistant",
            goal="Answer questions about Mark's badminton availability.",
            backstory=(
                "You are a scheduling assistant responsible for checking Mark's "
                "calendar and answering availability questions."
            ),
            tools=[AvailabilityTool()],
            llm=self.llm,
        )

    async def invoke(self, user_question: str) -> str:
        """Run a single CrewAI task and return the text result."""
        task = Task(
            description=f"Answer this scheduling question: {user_question!r}",
            expected_output="A concise answer describing Mark's availability.",
            agent=self.agent,
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
        )

        try:
            result = await asyncio.to_thread(crew.kickoff)
        except Exception as exc:  # noqa: BLE001 - return readable failure to caller
            return f"Unable to process scheduling request: {exc}"

        return str(result).strip() if result else "No response available."
