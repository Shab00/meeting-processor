from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol

AGENT_URL = "http://localhost:8000"


def get_agent_card() -> AgentCard:
    # a2a-sdk v1.x has no top-level AgentCard.url; the endpoint is declared
    # via supported_interfaces instead.
    return AgentCard(
        name="meeting-processor",
        description="Turns meeting transcripts into a summary, action items, "
        "decisions and risks.",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=AGENT_URL,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="analyse_meeting",
                name="Analyse Meeting",
                description="Extract action items, decisions, risks from a transcript.",
                tags=["meetings", "extraction"],
                input_modes=["text/plain"],
                output_modes=["application/json"],
            )
        ],
    )
