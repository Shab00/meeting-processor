from agents import Agent, RunResult, Runner, handoff, set_default_openai_key

from app.config import settings
from app.agents.action_items import action_items_agent
from app.agents.decisions import decisions_agent
from app.agents.risks import risks_agent
from app.agents.summary import summary_agent

# pydantic-settings reads .env without exporting to os.environ, so hand the
# key to the SDK explicitly. Constructing agents does not call the API.
set_default_openai_key(settings.openai_api_key)

triage_agent = Agent(
    name="Triage",
    instructions=(
        "You receive a meeting transcript. Identify which specialists are "
        "needed and hand off to them. Always hand off to summary, then "
        "to action_items, then decisions, then risks, in that order."
    ),
    model=settings.agent_model,
    handoffs=[
        handoff(action_items_agent),
        handoff(decisions_agent),
        handoff(risks_agent),
        handoff(summary_agent),
    ],
)


async def run_triage(transcript: str) -> RunResult:
    result = await Runner.run(triage_agent, input=transcript)
    return result
