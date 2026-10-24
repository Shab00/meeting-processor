from agents import Agent

from app.config import settings
from app.models import ActionItem

action_items_agent = Agent(
    name="ActionItemExtractor",
    handoff_description="Extracts action items (owner, task, due date, quote).",
    instructions=(
        "Extract every action item from the transcript. "
        "For each: owner, task, due date if mentioned, "
        "and the exact quote from the transcript that supports it. "
        "Return ONLY the action items."
    ),
    model=settings.agent_model,
    output_type=list[ActionItem],
)
