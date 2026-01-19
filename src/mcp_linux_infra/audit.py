"""Audit logging structuré pour traçabilité complète."""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .config import CONFIG


class LogLevel(str, Enum):
    """Niveaux de log."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    """Types d'événements auditables."""

    SSH_CONNECT = "ssh_connect"
    SSH_DISCONNECT = "ssh_disconnect"
    SSH_COMMAND = "ssh_command"
    PRA_PROPOSED = "pra_proposed"
    PRA_APPROVED = "pra_approved"
    PRA_REJECTED = "pra_rejected"
    PRA_EXECUTED = "pra_executed"
    PRA_FAILED = "pra_failed"
    TOOL_CALL = "tool_call"
    TOOL_SUCCESS = "tool_success"
    TOOL_ERROR = "tool_error"
    SECURITY_VIOLATION = "security_violation"


class Status(str, Enum):
    """Statuts d'exécution."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    DENIED = "denied"


class AuditLogger:
    """Logger structuré pour audit trail."""

    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("mcp_linux_infra.audit")
        self._setup_handlers()

    def _setup_handlers(self):
        """Configure log handlers."""
        self.logger.setLevel(getattr(logging, CONFIG.log_level))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (structured JSON)
        if CONFIG.log_dir:
            CONFIG.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = CONFIG.log_dir / f"mcp-audit-{datetime.now():%Y%m%d}.json"

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)

    def log_event(
        self,
        event_type: EventType,
        status: Status,
        details: dict[str, Any],
        level: LogLevel = LogLevel.INFO,
    ):
        """Log structured audit event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "status": status.value,
            "details": self._sanitize(details),
        }

        log_method = getattr(self.logger, level.value.lower())
        log_method(json.dumps(event))

    def _sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive information from logs."""
        SENSITIVE_KEYS = {
            "password",
            "passphrase",
            "token",
            "secret",
            "key",
            "api_key",
            "private_key",
        }

        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize(value)
            else:
                sanitized[key] = value

        return sanitized


# Global audit logger
audit = AuditLogger()


# Convenience functions
def log_ssh_connect(
    host: str, username: str, status: Status, reused: bool = False, error: str | None = None
):
    """Log SSH connection attempt."""
    audit.log_event(
        EventType.SSH_CONNECT,
        status,
        {
            "host": host,
            "username": username,
            "reused": reused,
            "error": error,
        },
    )


def log_ssh_command(
    host: str, username: str, command: list[str], status: Status, returncode: int, error: str | None = None
):
    """Log SSH command execution."""
    audit.log_event(
        EventType.SSH_COMMAND,
        status,
        {
            "host": host,
            "username": username,
            "command": " ".join(command),
            "returncode": returncode,
            "error": error,
        },
    )


def log_pra_action(
    action: str,
    host: str,
    event_type: EventType,
    status: Status,
    approver: str | None = None,
    rationale: str | None = None,
    result: dict | None = None,
    error: str | None = None,
):
    """Log PRA action lifecycle."""
    audit.log_event(
        event_type,
        status,
        {
            "action": action,
            "host": host,
            "approver": approver,
            "rationale": rationale,
            "result": result,
            "error": error,
        },
        level=LogLevel.WARNING if status == Status.FAILURE else LogLevel.INFO,
    )


def log_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    status: Status,
    result: Any = None,
    error: str | None = None,
    duration_ms: float | None = None,
):
    """Log MCP tool call."""
    event_type = EventType.TOOL_SUCCESS if status == Status.SUCCESS else EventType.TOOL_ERROR

    audit.log_event(
        event_type,
        status,
        {
            "tool": tool_name,
            "parameters": parameters,
            "duration_ms": duration_ms,
            "result_preview": str(result)[:200] if result else None,
            "error": error,
        },
    )


def log_security_violation(
    violation_type: str, details: dict[str, Any], host: str | None = None
):
    """Log security violation."""
    audit.log_event(
        EventType.SECURITY_VIOLATION,
        Status.DENIED,
        {
            "violation_type": violation_type,
            "host": host,
            **details,
        },
        level=LogLevel.CRITICAL,
    )
