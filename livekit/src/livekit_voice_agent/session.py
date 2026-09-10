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
    current_role: Role = "receptionist"
    agents: dict[Role, "CompanyAgent"] = field(default_factory=dict)