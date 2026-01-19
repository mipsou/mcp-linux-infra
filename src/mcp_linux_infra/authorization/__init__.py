"""
Authorization system for SSH command execution

This module provides a whitelist-based authorization system with three levels:
- AUTO: Execute immediately (read-only commands)
- MANUAL: Require human approval before execution
- BLOCKED: Refuse execution (dangerous commands)
"""

from .models import AuthLevel, CommandRule, CommandAuthorization
from .whitelist import COMMAND_WHITELIST, load_whitelist_from_yaml
from .engine import AuthorizationEngine

__all__ = [
    "AuthLevel",
    "CommandRule",
    "CommandAuthorization",
    "COMMAND_WHITELIST",
    "load_whitelist_from_yaml",
    "AuthorizationEngine",
]
