from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routes import analyse, meetings

# Single Limiter instance shared with the @limiter.limit decorators.
limiter = analyse.limiter
app = FastAPI(title="Meeting Processor", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse.router)
app.include_router(meetings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
