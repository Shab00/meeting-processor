from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from a2a_server import mount_a2a
from app.config import settings
from app.routes import analyse, meetings

# Single Limiter instance shared with the @limiter.limit decorators.
limiter = analyse.limiter
app = FastAPI(title="Meeting Processor", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://shab00.github.io",
        "http://localhost:4000",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(analyse.router)
app.include_router(meetings.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Mounted last so A2A routes (POST /, agent card) never shadow the REST API.
mount_a2a(app)
