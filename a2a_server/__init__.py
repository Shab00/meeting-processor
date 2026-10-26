"""A2A (Agent2Agent) server exposing meeting analysis as an agent skill."""

from a2a_server.routes import mount_a2a

__all__ = ["mount_a2a"]
