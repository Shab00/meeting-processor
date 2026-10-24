import uuid
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db import Base

# ---------------------------------------------------------------------------
# Pydantic schemas (API + agent outputs)
# ---------------------------------------------------------------------------


class ActionItem(BaseModel):
    owner: str
    task: str
    due_date: str | None = None
    source_quote: str


class Decision(BaseModel):
    description: str
    made_by: str | None = None
    source_quote: str


class Risk(BaseModel):
    description: str
    severity: Literal["low", "medium", "high"]
    source_quote: str


class MeetingAnalysis(BaseModel):
    summary: str
    action_items: list[ActionItem]
    decisions: list[Decision]
    risks: list[Risk]


class AnalyseRequest(BaseModel):
    title: str
    transcript: str


class AnalyseResponse(BaseModel):
    meeting_id: UUID
    analysis: MeetingAnalysis


class MeetingOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    analysis: MeetingAnalysis | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# SQLAlchemy models
# ---------------------------------------------------------------------------


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    transcript = Column(String, nullable=False)
    analysis = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
