from app.models import MeetingAnalysis

MIN_TRANSCRIPT_CHARS = 100
MAX_TRANSCRIPT_CHARS = 50_000


def validate_input(transcript: str) -> None:
    if len(transcript) < MIN_TRANSCRIPT_CHARS:
        raise ValueError("Transcript too short (< 100 chars)")
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        raise ValueError("Transcript too long (> 50,000 chars)")


def validate_output(analysis: MeetingAnalysis) -> None:
    if not analysis.summary or not analysis.summary.strip():
        raise ValueError("Missing summary")
    # basic structural validation — Pydantic already enforces types
