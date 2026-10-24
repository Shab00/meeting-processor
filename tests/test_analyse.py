import os

# Settings() requires these at import time; dummy values, nothing connects.
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

import uuid  # noqa: E402
from datetime import datetime  # noqa: E402
from unittest.mock import AsyncMock, MagicMock  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    ActionItem,
    AnalyseResponse,
    Decision,
    Meeting,
    MeetingAnalysis,
    Risk,
)

TRANSCRIPT = (
    "Alice: Let's ship the beta on Friday. Bob: Agreed, I'll update the docs "
    "by Thursday. Carol: The payment API is still flaky, that's a risk."
)

FAKE_ANALYSIS = MeetingAnalysis(
    summary="The team agreed to ship the beta on Friday. Bob owns docs. "
    "Payment API flakiness is a risk.",
    action_items=[
        ActionItem(
            owner="Bob",
            task="Update the docs",
            due_date="Thursday",
            source_quote="I'll update the docs by Thursday",
        )
    ],
    decisions=[
        Decision(
            description="Ship the beta on Friday",
            made_by="Alice",
            source_quote="Let's ship the beta on Friday",
        )
    ],
    risks=[
        Risk(
            description="Payment API is flaky",
            severity="medium",
            source_quote="The payment API is still flaky",
        )
    ],
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    meeting_id = uuid.uuid4()

    # Simulate what the DB does on commit/refresh: populate server defaults.
    def fake_refresh(obj):
        obj.id = meeting_id
        obj.created_at = datetime.utcnow()

    db.refresh.side_effect = fake_refresh
    db.meeting_id = meeting_id

    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


@pytest.fixture
def mock_run_and_parse(monkeypatch):
    mock = AsyncMock(return_value=FAKE_ANALYSIS)
    monkeypatch.setattr("app.routes.analyse.run_and_parse", mock)
    return mock


@pytest.fixture
def client():
    return TestClient(app)


def test_analyse_returns_response_and_saves_meeting(client, mock_db, mock_run_and_parse):
    r = client.post("/analyse", json={"title": "Beta sync", "transcript": TRANSCRIPT})

    assert r.status_code == 200, r.text
    body = AnalyseResponse.model_validate(r.json())
    assert body.meeting_id == mock_db.meeting_id
    assert body.analysis == FAKE_ANALYSIS

    mock_run_and_parse.assert_awaited_once_with(TRANSCRIPT)

    mock_db.add.assert_called_once()
    saved = mock_db.add.call_args.args[0]
    assert isinstance(saved, Meeting)
    assert saved.title == "Beta sync"
    assert saved.transcript == TRANSCRIPT
    assert saved.analysis == FAKE_ANALYSIS.model_dump()
    mock_db.commit.assert_called_once()


def test_analyse_rejects_short_transcript(client, mock_db, mock_run_and_parse):
    r = client.post("/analyse", json={"title": "Too short", "transcript": "hi"})

    assert r.status_code == 422
    assert "too short" in r.json()["detail"].lower()
    mock_run_and_parse.assert_not_awaited()
    mock_db.add.assert_not_called()


def test_analyse_rejects_empty_summary(client, mock_db, monkeypatch):
    bad = FAKE_ANALYSIS.model_copy(update={"summary": ""})
    monkeypatch.setattr("app.routes.analyse.run_and_parse", AsyncMock(return_value=bad))

    r = client.post("/analyse", json={"title": "Beta sync", "transcript": TRANSCRIPT})

    assert r.status_code == 502
    mock_db.add.assert_not_called()
