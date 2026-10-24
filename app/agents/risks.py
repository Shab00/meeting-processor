from agents import Agent

from app.config import settings
from app.models import Risk

risks_agent = Agent(
    name="RiskExtractor",
    handoff_description="Extracts risks, blockers and concerns with severity.",
    instructions=(
        "Extract every risk, blocker or concern raised in the transcript. "
        "For each: a description, a severity of low, medium or high, "
        "and the exact quote from the transcript that supports it. "
        "Return ONLY the risks."
    ),
    model=settings.agent_model,
    output_type=list[Risk],
)
