import asyncio
from typing import Any

from agents import Agent, Runner
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.agents.action_items import action_items_agent
from app.agents.decisions import decisions_agent
from app.agents.guardrails import validate_input, validate_output
from app.agents.risks import risks_agent
from app.agents.summary import summary_agent
from app.agents.triage import run_triage
from app.db import get_db
from app.models import AnalyseRequest, AnalyseResponse, Meeting, MeetingAnalysis

# Defined here (not in main.py) so the decorator below and app.state.limiter
# share one instance without a circular import.
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["analyse"])

# Specialist agent -> MeetingAnalysis field it populates.
SPECIALISTS: dict[str, Agent] = {
    "summary": summary_agent,
    "action_items": action_items_agent,
    "decisions": decisions_agent,
    "risks": risks_agent,
}


async def run_and_parse(transcript: str) -> MeetingAnalysis:
    """Run the triage agent and coerce the result into a MeetingAnalysis.

    TODO: In the openai-agents SDK a handoff transfers control for the rest of
    the run, so a single triage run ends with ONE specialist's output — it
    cannot chain summary -> action_items -> decisions -> risks. Best effort:
    use whichever specialist triage handed off to, then run the remaining
    specialists directly (concurrently) to fill the other fields. Revisit
    (e.g. specialists as tools via Agent.as_tool, or drop triage) once we
    have real transcripts to evaluate against.
    """
    outputs: dict[str, Any] = {}

    result = await run_triage(transcript)
    for field, agent in SPECIALISTS.items():
        if result.last_agent is agent:
            outputs[field] = result.final_output
            break

    missing = [field for field in SPECIALISTS if field not in outputs]
    results = await asyncio.gather(
        *(Runner.run(SPECIALISTS[field], input=transcript) for field in missing)
    )
    for field, r in zip(missing, results):
        outputs[field] = r.final_output

    # Specialists return Pydantic objects / str already; model_validate
    # re-checks the combined shape.
    return MeetingAnalysis.model_validate(outputs)


@router.post("/analyse", response_model=AnalyseResponse)
@limiter.limit("10/minute")
async def analyse_endpoint(
    request: Request,  # required by slowapi
    req: AnalyseRequest,
    db: Session = Depends(get_db),
) -> AnalyseResponse:
    try:
        validate_input(req.transcript)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        analysis = await run_and_parse(req.transcript)
        validate_output(analysis)
    except ValueError as e:
        # Includes pydantic.ValidationError (a ValueError subclass).
        raise HTTPException(status_code=502, detail=f"Agent output invalid: {e}")

    meeting = Meeting(
        title=req.title,
        transcript=req.transcript,
        analysis=analysis.model_dump(),
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return AnalyseResponse(meeting_id=meeting.id, analysis=analysis)
