from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI

from a2a_server.agent_card import get_agent_card
from a2a_server.executor import MeetingProcessorExecutor


def mount_a2a(app: FastAPI) -> None:
    """Serve the agent card at /.well-known/agent-card.json and JSON-RPC at POST /."""
    agent_card = get_agent_card()
    handler = DefaultRequestHandler(
        MeetingProcessorExecutor(), InMemoryTaskStore(), agent_card
    )
    # In a2a-sdk v1.x the helper takes pre-built route lists rather than
    # (app, card, handler).
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(agent_card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )
