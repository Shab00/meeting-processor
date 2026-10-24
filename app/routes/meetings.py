from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Meeting, MeetingOut

router = APIRouter(tags=["meetings"])


@router.get("/meetings", response_model=list[MeetingOut])
def list_meetings(db: Session = Depends(get_db)) -> list[MeetingOut]:
    rows = (
        db.query(Meeting.id, Meeting.title, Meeting.created_at)
        .order_by(Meeting.created_at.desc())
        .all()
    )
    return [
        MeetingOut(id=r.id, title=r.title, created_at=r.created_at, analysis=None)
        for r in rows
    ]


@router.get("/meetings/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: UUID, db: Session = Depends(get_db)) -> MeetingOut:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingOut.model_validate(meeting)
