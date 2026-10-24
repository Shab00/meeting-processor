from agents import Agent

from app.config import settings
from app.models import Decision

decisions_agent = Agent(
    name="DecisionExtractor",
    handoff_description="Extracts decisions made in the meeting.",
    instructions=(
        "Extract every decision made in the transcript. "
        "For each: a description of the decision, who made it if stated, "
        "and the exact quote from the transcript that supports it. "
        "Return ONLY the decisions."
    ),
    model=settings.agent_model,
    output_type=list[Decision],
)
