"""Configuration centralisée pour MCP Linux Infra."""

import getpass
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

UpperCase = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Config(BaseSettings):
    """Configuration globale chargée depuis variables d'environnement."""

    model_config = SettingsConfigDict(
        env_prefix="LINUX_MCP_",
        env_ignore_empty=True,
        case_sensitive=False,
    )

    # User management
    user: str = Field(default_factory=getpass.getuser, description="Default SSH user")

    # SSH Configuration - Read-only (diagnostics)
    ssh_key_path: Path | None = Field(
        default=None, description="Path to mcp-reader SSH private key"
    )
    search_for_ssh_key: bool = Field(
        default=False, description="Auto-search for SSH keys in ~/.ssh"
    )
    key_passphrase: str | None = Field(
        default=None, description="Passphrase for encrypted SSH keys"
    )

    # SSH Configuration - PRA Exec (actions)
    pra_key_path: Path | None = Field(
        default=None, description="Path to pra-exec SSH private key"
    )
    pra_user: str = Field(default="pra-runner", description="PRA execution SSH user")
    pra_key_passphrase: str | None = Field(
        default=None, description="Passphrase for PRA key"
    )

    # Connection pooling
    ssh_connection_timeout: int = Field(
        default=30, description="SSH connection timeout in seconds"
    )
    ssh_keepalive_interval: int = Field(
        default=60, description="SSH keepalive interval in seconds"
    )
    ssh_max_connections: int = Field(
        default=10, description="Maximum concurrent SSH connections"
    )

    # Logging
    log_dir: Path | None = Field(default=None, description="Directory for log files")
    log_level: UpperCase = Field(default="INFO", description="Logging level")
    log_retention_days: int = Field(
        default=30, description="Log file retention period"
    )

    # Security
    allowed_log_paths: str | None = Field(
        default="/var/log/*", description="Whitelist for log file paths (glob pattern)"
    )
    allowed_hosts: str | None = Field(
        default=None,
        description="Whitelist for allowed hosts (comma-separated, * for all)",
    )
    require_approval_for_pra: bool = Field(
        default=True, description="Require human approval for PRA actions"
    )

    # PRA Configuration
    pra_audit_log: Path = Field(
        default=Path("/var/log/mcp-pra.log"),
        description="PRA audit log path on MCP server",
    )
    pra_max_impact: Literal["low", "medium", "high"] = Field(
        default="medium", description="Maximum allowed impact level for auto-actions"
    )

    # Diagnostics
    default_log_lines: int = Field(
        default=100, description="Default number of log lines to fetch"
    )
    default_command_timeout: int = Field(
        default=120, description="Default command timeout in seconds"
    )

    @field_validator("ssh_key_path", "pra_key_path", "log_dir")
    @classmethod
    def expand_path(cls, v: Path | None) -> Path | None:
        """Expand ~ and environment variables in paths."""
        if v is None:
            return None
        return Path(os.path.expandvars(os.path.expanduser(str(v))))

    @field_validator("allowed_hosts")
    @classmethod
    def parse_allowed_hosts(cls, v: str | None) -> list[str] | None:
        """Parse comma-separated allowed hosts."""
        if v is None or v == "*":
            return None  # All hosts allowed
        return [h.strip() for h in v.split(",") if h.strip()]

    def is_host_allowed(self, host: str) -> bool:
        """Check if host is in allowed list."""
        if self.allowed_hosts is None:
            return True
        return host in self.allowed_hosts


# Global singleton configuration
CONFIG = Config()


def get_settings() -> Config:
    """Get the global configuration instance."""
    return CONFIG
