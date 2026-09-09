from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .roles import CompanyAgent

Role = Literal[
    "receptionist",
    "hr",
    "manager",
    "team_lead",
]


@dataclass
class SessionState:
    """
    Shared state for the complete voice session.

    The agents dictionary contains pre-instantiated specialist agents.
    current_role is kept as an explicit application-level state variable
    for observability and validation.
    """

    current_role: Role = "receptionist"
    agents: dict[Role, "CompanyAgent"] = field(default_factory=dict)