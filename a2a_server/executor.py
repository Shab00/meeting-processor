import logging

from a2a.helpers import new_task_from_user_message, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part
from a2a.utils.errors import UnsupportedOperationError

from app.agents.guardrails import validate_input, validate_output
from app.routes.analyse import run_and_parse

logger = logging.getLogger(__name__)


class MeetingProcessorExecutor(AgentExecutor):
    """Runs the same pipeline as POST /analyse, without persisting a Meeting."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        if not context.current_task:
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        logger.info("A2A task %s: analyse_meeting started", task.id)

        transcript = context.get_user_input()
        try:
            # Same guardrails as the REST endpoint so A2A is not a bypass.
            validate_input(transcript)
            await updater.start_work()
            analysis = await run_and_parse(transcript)
            validate_output(analysis)
        except ValueError as e:
            logger.warning("A2A task %s failed: %s", task.id, e)
            await updater.failed(
                new_text_message(str(e), context_id=task.context_id, task_id=task.id)
            )
            return

        await updater.add_artifact(
            [Part(text=analysis.model_dump_json(), media_type="application/json")],
            name="meeting_analysis",
        )
        await updater.complete()
        logger.info("A2A task %s: analyse_meeting completed", task.id)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # a2a-sdk v1.x dropped ServerError; A2AError subclasses are raised directly.
        raise UnsupportedOperationError()
