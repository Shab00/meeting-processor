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
| GET    | `/.well-known/agent-card.json` | A2A agent card (skill `analyse_meeting`)        |
| POST   | `/`              | A2A JSON-RPC endpoint (`SendMessage`, `GetTask`, ...)          |

## A2A

The service is also an A2A (Agent2Agent, a2a-sdk 1.x) server, in `a2a_server/`. Send a text message containing the transcript and the task completes with one `application/json` artifact holding a serialised `MeetingAnalysis`. It runs the same `run_and_parse` pipeline and input/output guardrails as `/analyse`, but it does **not** store a `Meeting` row (A2A requests carry no title) and is not rate limited. The task store is in-memory, so tasks are lost on restart. Cancellation is not supported.

The agent card advertises `http://localhost:8000` (`a2a_server/agent_card.py`). Change it before deploying.

Clients: `meeting-chat` and `meeting-followup` each include an `a2a_client/` package.

## Design decisions

- **Triage + specialists.** A triage agent can hand off to four narrow specialists (summary, action items, decisions, risks), each with its own focused prompt and typed `output_type`. In the Agents SDK a handoff transfers control for the rest of the run, so one triage run produces only one specialist's output. `run_and_parse` uses that output and runs the remaining specialists directly, in parallel. See the TODO in `app/routes/analyse.py`.
- **Pydantic output guardrails.** Every specialist returns a Pydantic type (`list[ActionItem]`, `list[Decision]`, `list[Risk]`, `str`). The SDK enforces these as strict JSON schemas. The combined result is validated as `MeetingAnalysis`, and `validate_output` adds semantic checks such as requiring a non-empty summary.
- **Input guardrails.** Transcripts must be between 100 and 50,000 characters.
- **Grounding.** Every extracted item carries a `source_quote` from the transcript so it can be audited.

## Not here yet

- Follow-up workflow
- Chat agent over past meetings
- Database migrations and a real database connection
