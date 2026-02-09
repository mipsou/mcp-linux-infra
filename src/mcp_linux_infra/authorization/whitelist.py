"""
Command whitelist configuration

Defines which commands can be executed and at what authorization level.
"""

from typing import List
import yaml
from pathlib import Path

from .models import AuthLevel, CommandRule


# Default command whitelist
COMMAND_WHITELIST: List[CommandRule] = [
    # ═══════════════════════════════════════════════════
    # AUTO - Read-Only Commands (via mcp-reader)
    # ═══════════════════════════════════════════════════
    CommandRule(
        pattern=r"^systemctl status\s+",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Check service status",
        rationale="Read-only, no system impact"
    ),
    CommandRule(
        pattern=r"^systemctl list-units",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="List system units",
        rationale="Read-only, diagnostic"
    ),
    CommandRule(
        pattern=r"^journalctl\s+",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Read system logs",
        rationale="Read-only, diagnostic purpose"
    ),
    CommandRule(
        pattern=r"^ss\s+-[lntup]+",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="List network connections",
        rationale="Read-only network diagnostic"
    ),
    CommandRule(
        pattern=r"^df\s+-h",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Check disk usage",
        rationale="Read-only system info"
    ),
    CommandRule(
        pattern=r"^free\s+-h",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Check memory usage",
        rationale="Read-only system info"
    ),
    CommandRule(
        pattern=r"^uptime",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Check system uptime",
        rationale="Read-only system info"
    ),
    CommandRule(
        pattern=r"^cat\s+/var/log/",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Read log files",
        rationale="Read-only, diagnostic"
    ),
    CommandRule(
        pattern=r"^podman\s+ps",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="List containers",
        rationale="Read-only container info"
    ),
    CommandRule(
        pattern=r"^podman\s+inspect\s+",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Inspect container",
        rationale="Read-only container info"
    ),
    CommandRule(
        pattern=r"^ansible-playbook\s+.*--check",
        auth_level=AuthLevel.AUTO,
        ssh_user="mcp-reader",
        description="Ansible dry-run (check mode)",
        rationale="Read-only, no system changes"
    ),

    # ═══════════════════════════════════════════════════
    # MANUAL - Requires Approval (via exec-runner)
    # ═══════════════════════════════════════════════════
    CommandRule(
        pattern=r"^systemctl restart\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Restart system service",
        rationale="Service interruption, needs approval"
    ),
    CommandRule(
        pattern=r"^systemctl reload\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Reload service configuration",
        rationale="Config change, minimal impact but needs review"
    ),
    CommandRule(
        pattern=r"^systemctl start\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Start system service",
        rationale="System state change"
    ),
    CommandRule(
        pattern=r"^systemctl stop\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Stop system service",
        rationale="Service interruption"
    ),
    CommandRule(
        pattern=r"^podman restart\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Restart container",
        rationale="Service interruption"
    ),
    CommandRule(
        pattern=r"^podman stop\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Stop container",
        rationale="Service interruption"
    ),
    CommandRule(
        pattern=r"^podman start\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Start container",
        rationale="System state change"
    ),
    CommandRule(
        pattern=r"^ansible-playbook\s+(?!.*--check)",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Execute Ansible playbook",
        rationale="Infrastructure changes, needs approval"
    ),
    CommandRule(
        pattern=r"^reboot$",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Reboot system",
        rationale="CRITICAL: Full system restart"
    ),
    CommandRule(
        pattern=r"^shutdown\s+",
        auth_level=AuthLevel.MANUAL,
        ssh_user="exec-runner",
        description="Shutdown system",
        rationale="CRITICAL: System shutdown"
    ),

    # ═══════════════════════════════════════════════════
    # BLOCKED - Dangerous Commands
    # ═══════════════════════════════════════════════════
    CommandRule(
        pattern=r".*rm\s+-rf\s+/(?!tmp|var/tmp)",
        auth_level=AuthLevel.BLOCKED,
        ssh_user="none",
        description="Recursive delete from root",
        rationale="DANGEROUS: Could destroy system"
    ),
    CommandRule(
        pattern=r".*dd\s+.*of=/dev/[sv]d",
        auth_level=AuthLevel.BLOCKED,
        ssh_user="none",
        description="Direct disk write",
        rationale="DANGEROUS: Could corrupt filesystem"
    ),
    CommandRule(
        pattern=r".*mkfs\.",
        auth_level=AuthLevel.BLOCKED,
        ssh_user="none",
        description="Format filesystem",
        rationale="DANGEROUS: Data loss"
    ),
    CommandRule(
        pattern=r".*fdisk\s+",
        auth_level=AuthLevel.BLOCKED,
        ssh_user="none",
        description="Partition disk",
        rationale="DANGEROUS: Could corrupt partitions"
    ),
    CommandRule(
        pattern=r".*:\(\)\{.*:\|:.*\};:",
        auth_level=AuthLevel.BLOCKED,
        ssh_user="none",
        description="Fork bomb",
        rationale="DANGEROUS: DoS attack"
    ),
]


def load_whitelist_from_yaml(yaml_path: Path) -> List[CommandRule]:
    """
    Load command whitelist from YAML file

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        List of CommandRule objects

    Example YAML format:
        auto_approved:
          - pattern: "^systemctl status "
            description: "Check service status"
            ssh_user: "mcp-reader"
            rationale: "Read-only"

        manual_approval:
          - pattern: "^systemctl restart "
            description: "Restart service"
            ssh_user: "exec-runner"
            rationale: "Service interruption"

        blocked:
          - pattern: ".*rm -rf /.*"
            description: "Recursive delete"
            ssh_user: "none"
            rationale: "Dangerous"
    """

    if not yaml_path.exists():
        # Return default whitelist if file doesn't exist
        return COMMAND_WHITELIST

    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    whitelist = []

    # Load AUTO commands
    for cmd in config.get('auto_approved', []):
        whitelist.append(CommandRule(
            pattern=cmd['pattern'],
            auth_level=AuthLevel.AUTO,
            ssh_user=cmd['ssh_user'],
            description=cmd['description'],
            rationale=cmd['rationale']
        ))

    # Load MANUAL commands
    for cmd in config.get('manual_approval', []):
        whitelist.append(CommandRule(
            pattern=cmd['pattern'],
            auth_level=AuthLevel.MANUAL,
            ssh_user=cmd['ssh_user'],
            description=cmd['description'],
            rationale=cmd['rationale']
        ))

    # Load BLOCKED commands
    for cmd in config.get('blocked', []):
        whitelist.append(CommandRule(
            pattern=cmd['pattern'],
            auth_level=AuthLevel.BLOCKED,
            ssh_user=cmd.get('ssh_user', 'none'),
            description=cmd['description'],
            rationale=cmd['rationale']
        ))

    return whitelist
