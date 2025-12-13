"""A2A executor wrapper for Jeff's participant agent."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart

from agent import JeffAgent


class JeffAgentExecutor(AgentExecutor):
    """Bridges A2A request execution to the LangChain-backed Jeff agent."""

    def __init__(self) -> None:
        self.agent = JeffAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        query = context.get_user_input() or ""
        try:
            response_text = await self.agent.get_response(
                query=query,
                context_id=context.context_id,
            )
        except Exception as exc:  # noqa: BLE001 - return an explicit failure message to caller
            response_text = f"Unable to process scheduling request: {exc}"

        parts = [Part(root=TextPart(text=response_text))]
        await updater.add_artifact(parts, name="scheduling_result")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return
