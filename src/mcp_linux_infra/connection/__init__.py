"""Connection management module."""

# Smart SSH Manager avec fallback automatique Agent → Direct
from .smart_ssh import (
    SSHConnectionError,
    SSHAuthMode,
    SmartSSHManager,
    execute_command,
    execute_pra_action,
    get_current_auth_mode,
    get_smart_ssh_manager,
)

__all__ = [
    "SmartSSHManager",
    "SSHConnectionError",
    "SSHAuthMode",
    "get_smart_ssh_manager",
    "get_current_auth_mode",
    "execute_command",
    "execute_pra_action",
]
