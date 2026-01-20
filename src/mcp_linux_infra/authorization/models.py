"""
Data models for the authorization system
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class AuthLevel(Enum):
    """Authorization levels for commands"""
    AUTO = "auto"           # Execute immediately (read-only)
    MANUAL = "manual"       # Require human approval
    BLOCKED = "blocked"     # Refuse execution


@dataclass
class CommandRule:
    """Rule for command authorization"""
    pattern: str                    # Regex pattern to match command
    auth_level: AuthLevel          # Authorization level
    description: str               # Human-readable description
    ssh_user: str                  # SSH user to use (mcp-reader or exec-runner)
    rationale: str                 # Why this authorization level?

    def __post_init__(self):
        # Convert string to AuthLevel if needed
        if isinstance(self.auth_level, str):
            self.auth_level = AuthLevel(self.auth_level)


@dataclass
class CommandAuthorization:
    """Result of authorization check"""
    allowed: bool                           # Can execute now?
    auth_level: AuthLevel                   # Authorization level
    ssh_user: Optional[str] = None          # SSH user to use
    needs_approval: bool = False            # Needs human approval?
    approval_id: Optional[str] = None       # Approval request ID
    reason: Optional[str] = None            # Why allowed/blocked
    rule: Optional[CommandRule] = None      # Matching rule


@dataclass
class PendingCommand:
    """Pending command awaiting approval"""
    id: str                                 # Unique approval ID
    host: str                               # Target host
    command: str                            # Command to execute
    ssh_user: str                           # SSH user
    rule: CommandRule                       # Matching rule
    created_at: datetime = field(default_factory=datetime.now)
    approved: bool = False
    executed: bool = False

    @classmethod
    def create(cls, host: str, command: str, ssh_user: str, rule: CommandRule) -> "PendingCommand":
        """Create a new pending command with unique ID"""
        return cls(
            id=f"cmd_{uuid.uuid4().hex[:8]}",
            host=host,
            command=command,
            ssh_user=ssh_user,
            rule=rule
        )
