"""
Authorization engine for command execution

Checks commands against whitelist and manages approval workflow.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime

from .models import (
    AuthLevel,
    CommandRule,
    CommandAuthorization,
    PendingCommand,
)


class AuthorizationEngine:
    """
    Engine for command authorization decisions

    Matches commands against whitelist rules and manages approval workflow.
    """

    def __init__(self, whitelist: List[CommandRule]):
        """
        Initialize authorization engine

        Args:
            whitelist: List of CommandRule objects defining allowed commands
        """
        self.whitelist = whitelist
        self.pending_approvals: Dict[str, PendingCommand] = {}

    def check_command(self, host: str, command: str, user: str = "unknown") -> CommandAuthorization:
        """
        Check if a command is authorized for execution

        Args:
            host: Target host
            command: Command to check
            user: User attempting to execute (for learning stats)

        Returns:
            CommandAuthorization with decision and metadata
        """

        # Check against whitelist (first match wins)
        for rule in self.whitelist:
            if re.match(rule.pattern, command):
                return self._process_rule_match(host, command, rule)

        # No match = default BLOCK
        # Record for auto-learning
        try:
            from ..analysis.auto_learning import record_blocked_command
            record_blocked_command(command, user=user, host=host)
        except Exception:
            pass  # Don't fail if learning system has issues

        return CommandAuthorization(
            allowed=False,
            auth_level=AuthLevel.BLOCKED,
            reason="Command not in whitelist (default deny policy)"
        )

    def _process_rule_match(
        self,
        host: str,
        command: str,
        rule: CommandRule
    ) -> CommandAuthorization:
        """Process a matched rule"""

        # BLOCKED - refuse immediately
        if rule.auth_level == AuthLevel.BLOCKED:
            return CommandAuthorization(
                allowed=False,
                auth_level=AuthLevel.BLOCKED,
                reason=f"BLOCKED: {rule.rationale}",
                rule=rule
            )

        # AUTO - allow immediately
        elif rule.auth_level == AuthLevel.AUTO:
            return CommandAuthorization(
                allowed=True,
                auth_level=AuthLevel.AUTO,
                ssh_user=rule.ssh_user,
                needs_approval=False,
                reason=f"Auto-approved: {rule.description}",
                rule=rule
            )

        # MANUAL - create approval request
        elif rule.auth_level == AuthLevel.MANUAL:
            pending = PendingCommand.create(
                host=host,
                command=command,
                ssh_user=rule.ssh_user,
                rule=rule
            )
            self.pending_approvals[pending.id] = pending

            return CommandAuthorization(
                allowed=False,
                auth_level=AuthLevel.MANUAL,
                ssh_user=rule.ssh_user,
                needs_approval=True,
                approval_id=pending.id,
                reason=f"Approval required: {rule.description}",
                rule=rule
            )

    def approve_command(self, approval_id: str) -> Optional[PendingCommand]:
        """
        Approve a pending command

        Args:
            approval_id: Approval request ID

        Returns:
            PendingCommand if found and approved, None otherwise
        """
        pending = self.pending_approvals.get(approval_id)

        if not pending:
            return None

        if pending.executed:
            return None  # Already executed

        pending.approved = True
        return pending

    def mark_executed(self, approval_id: str) -> bool:
        """
        Mark a pending command as executed

        Args:
            approval_id: Approval request ID

        Returns:
            True if marked, False if not found
        """
        pending = self.pending_approvals.get(approval_id)

        if not pending:
            return False

        pending.executed = True
        return True

    def get_pending(self, approval_id: str) -> Optional[PendingCommand]:
        """Get a pending command by ID"""
        return self.pending_approvals.get(approval_id)

    def get_all_pending(self) -> List[PendingCommand]:
        """Get all pending commands that haven't been executed"""
        return [
            p for p in self.pending_approvals.values()
            if not p.executed
        ]

    def cleanup_old_approvals(self, max_age_hours: int = 24):
        """
        Remove old approval requests

        Args:
            max_age_hours: Maximum age in hours to keep approvals
        """
        now = datetime.now()
        to_remove = []

        for approval_id, pending in self.pending_approvals.items():
            age_hours = (now - pending.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_remove.append(approval_id)

        for approval_id in to_remove:
            del self.pending_approvals[approval_id]

    def get_whitelist_summary(self) -> Dict[str, List[CommandRule]]:
        """
        Get whitelist organized by authorization level

        Returns:
            Dict with keys 'auto', 'manual', 'blocked'
        """
        summary = {
            'auto': [],
            'manual': [],
            'blocked': []
        }

        for rule in self.whitelist:
            if rule.auth_level == AuthLevel.AUTO:
                summary['auto'].append(rule)
            elif rule.auth_level == AuthLevel.MANUAL:
                summary['manual'].append(rule)
            elif rule.auth_level == AuthLevel.BLOCKED:
                summary['blocked'].append(rule)

        return summary
