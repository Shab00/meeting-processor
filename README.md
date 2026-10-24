# meeting-processor

A FastAPI service that turns meeting transcripts into a structured summary, action items, decisions and risks using OpenAI Agents.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY and DATABASE_URL
uvicorn app.main:app --reload
```

Run tests (no database or OpenAI key needed; agents and DB are mocked):

```bash
python -m pytest tests/ -v
```

Tables are not created automatically yet. Once a database is available, call `app.db.init_db()` to create them.

## API

| Method | Path             | Description                                                   |
|--------|------------------|---------------------------------------------------------------|
| POST   | `/analyse`       | Analyse a transcript (`{title, transcript}`) and store the result. Rate limited to 10/minute per IP. |
| GET    | `/meetings`      | List meetings (id, title, created_at)                         |
| GET    | `/meetings/{id}` | Get one meeting with its full analysis                        |
| GET    | `/health`        | Liveness check                                                |

## Design decisions

- **Triage + specialists.** A triage agent can hand off to four narrow specialists (summary, action items, decisions, risks), each with its own focused prompt and typed `output_type`. In the Agents SDK a handoff transfers control for the rest of the run, so one triage run produces only one specialist's output. `run_and_parse` uses that output and runs the remaining specialists directly, in parallel. See the TODO in `app/routes/analyse.py`.
- **Pydantic output guardrails.** Every specialist returns a Pydantic type (`list[ActionItem]`, `list[Decision]`, `list[Risk]`, `str`). The SDK enforces these as strict JSON schemas. The combined result is validated as `MeetingAnalysis`, and `validate_output` adds semantic checks such as requiring a non-empty summary.
- **Input guardrails.** Transcripts must be between 100 and 50,000 characters.
- **Grounding.** Every extracted item carries a `source_quote` from the transcript so it can be audited.

## Not here yet

- A2A (agent-to-agent) interface
- Follow-up workflow
- Chat agent over past meetings
- Database migrations and a real database connection
