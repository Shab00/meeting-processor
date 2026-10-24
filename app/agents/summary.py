from agents import Agent

from app.config import settings

summary_agent = Agent(
    name="Summariser",
    handoff_description="Writes a three-sentence summary of the meeting.",
    instructions=(
        "Summarise the meeting transcript in exactly three sentences. "
        "Cover the purpose, the main discussion points and the outcome. "
        "Return ONLY the summary text."
    ),
    model=settings.agent_model,
    output_type=str,
)
