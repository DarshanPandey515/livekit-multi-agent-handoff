from __future__ import annotations
import json
import logging
from collections.abc import Callable
from livekit.agents import Agent, ChatContext, RunContext, function_tool
from .prompts import ROLE_INSTRUCTIONS
from .session import Role, SessionState

logger = logging.getLogger(__name__)


class CompanyAgent(Agent):
    """
    Base agent used by every company department.

    Important:
        This class intentionally contains NO @function_tool methods.

    Transfer tools are standalone functions and are explicitly assigned
    to each role. This prevents an HR agent from receiving transfer_to_hr,
    a manager from receiving transfer_to_manager, etc.
    """

    def __init__(
        self,
        role: Role,
        chat_ctx: ChatContext | None = None,
        tools: list[object] | None = None,
    ) -> None:
        self.role = role

        super().__init__(
            instructions=ROLE_INSTRUCTIONS[role],
            chat_ctx=chat_ctx,
            tools=tools or [],
        )

    def compact_context(self) -> ChatContext:
        """
        Return a bounded conversation context for a handoff.

        Eight items is enough to preserve the recent conversational state
        without allowing repeated handoffs to grow the prompt indefinitely.
        """

        return (
            self.chat_ctx
            .copy(exclude_instructions=True)
            .truncate(max_items=8)
        )


TRANSFER_SPECS: dict[Role, tuple[str, str]] = {
    "hr": (
        "Transferring you to HR.",
        "Transfer the employee to the HR department. "
        "This tool is only registered on agents that are allowed to transfer "
        "TO HR. The HR agent itself never receives this tool.",
    ),
    "manager": (
        "Transferring you to the manager.",
        "Transfer the employee to the manager. "
        "This tool is never registered on the manager agent itself.",
    ),
    "team_lead": (
        "Transferring you to the team lead.",
        "Transfer the employee to the team lead. "
        "This tool is never registered on the team lead agent itself.",
    ),
}


async def publish_current_role(context: RunContext[SessionState], role: Role) -> None:
    """Broadcast the active role to the room so web clients can display it."""
    
    try:
        room = context.session.room_io.room
        await room.local_participant.set_metadata(json.dumps({"role": role}))
    except Exception:
        logger.warning("failed to publish current role to room", exc_info=True)


def make_transfer_tool(target_role: Role) -> Callable:
    """Build the transfer tool for a target role (single implementation)."""
    
    message, description = TRANSFER_SPECS[target_role]

    @function_tool(
        name=f"transfer_to_{target_role}",
        description=description,
    )
    async def transfer(
        context: RunContext[SessionState],
    ) -> tuple[CompanyAgent, str]:
        """
        Transfer the employee to another department.
        """

        state = context.userdata
        state.current_role = target_role
        await publish_current_role(context, target_role)
        return state.agents[target_role], message

    return transfer


transfer_to_hr = make_transfer_tool("hr")
transfer_to_manager = make_transfer_tool("manager")
transfer_to_team_lead = make_transfer_tool("team_lead")


def build_agents() -> dict[Role, CompanyAgent]:

    return {
        "receptionist": CompanyAgent(
            role="receptionist",
            tools=[
                transfer_to_hr,
                transfer_to_manager,
                transfer_to_team_lead,
            ],
        ),
        "hr": CompanyAgent(
            role="hr",
            tools=[
                transfer_to_manager,
                transfer_to_team_lead,
            ],
        ),
        "manager": CompanyAgent(
            role="manager",
            tools=[
                transfer_to_hr,
                transfer_to_team_lead,
            ],
        ),
        "team_lead": CompanyAgent(
            role="team_lead",
            tools=[
                transfer_to_hr,
                transfer_to_manager,
            ],
        ),
    }