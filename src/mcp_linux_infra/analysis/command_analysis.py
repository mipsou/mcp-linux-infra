"""Command safety analysis and risk assessment."""

import re
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from ..authorization.models import AuthLevel
from ..authorization.whitelist import COMMAND_WHITELIST


class RiskLevel(str, Enum):
    """Risk levels for commands."""
    CRITICAL = "CRITICAL"  # Destructive, dangerous
    HIGH = "HIGH"          # Significant system changes
    MEDIUM = "MEDIUM"      # Service restarts, configuration changes
    LOW = "LOW"            # Read-only, monitoring
    UNKNOWN = "UNKNOWN"    # Cannot determine


@dataclass
class CommandAnalysis:
    """Result of command analysis."""
    command: str
    risk_level: RiskLevel
    category: str
    is_readonly: bool
    suggested_level: Optional[AuthLevel]
    suggested_ssh_user: str
    rationale: str
    similar_commands: list[str]
    can_auto_add: bool
    recommended_action: str


# Known safe read-only commands
KNOWN_SAFE_COMMANDS = {
    # Monitoring tools
    'htop': {
        'category': 'monitoring',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Interactive process viewer (read-only)'
    },
    'top': {
        'category': 'monitoring',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Process monitor (read-only)'
    },
    'iotop': {
        'category': 'monitoring',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'I/O monitoring (read-only)'
    },
    'iftop': {
        'category': 'monitoring',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Network bandwidth monitor (read-only)'
    },
    'nethogs': {
        'category': 'monitoring',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Network traffic monitor per process (read-only)'
    },

    # Network tools
    'netstat': {
        'category': 'network',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Network connections status (read-only)'
    },
    'ip addr': {
        'category': 'network',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Show IP addresses (read-only)'
    },
    'ip route': {
        'category': 'network',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Show routing table (read-only)'
    },
    'ping': {
        'category': 'network',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Network connectivity test (read-only)'
    },
    'traceroute': {
        'category': 'network',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Network path tracing (read-only)'
    },

    # System info
    'hostname': {
        'category': 'system',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Show hostname (read-only)'
    },
    'uname': {
        'category': 'system',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'System information (read-only)'
    },
    'lsblk': {
        'category': 'system',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'List block devices (read-only)'
    },
    'lscpu': {
        'category': 'system',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'CPU information (read-only)'
    },
    'lsmem': {
        'category': 'system',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Memory information (read-only)'
    },

    # File operations (safe reads)
    'ls': {
        'category': 'filesystem',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'List directory contents (read-only)'
    },
    'head': {
        'category': 'filesystem',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Show file beginning (read-only)'
    },
    'tail': {
        'category': 'filesystem',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Show file end (read-only)'
    },
    'less': {
        'category': 'filesystem',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'File viewer (read-only)'
    },
    'grep': {
        'category': 'filesystem',
        'risk': RiskLevel.LOW,
        'level': AuthLevel.AUTO,
        'user': 'mcp-reader',
        'rationale': 'Text search (read-only)'
    },
}


# Dangerous command patterns
DANGEROUS_PATTERNS = [
    (r'.*rm\s+-rf\s+/', 'Recursive delete - use Ansible for safe cleanup'),
    (r'.*dd\s+.*of=/dev/', 'Direct disk write - extremely dangerous'),
    (r'.*mkfs\.', 'Format filesystem - data loss'),
    (r'.*fdisk\s+', 'Partition manipulation - data loss risk'),
    (r'.*parted\s+', 'Partition manipulation - data loss risk'),
    (r'.*wipefs\s+', 'Wipe filesystem signatures - data loss'),
    (r'.*:\(\)\{.*:\|:.*\};:', 'Fork bomb - DoS attack'),
    (r'.*>\s*/dev/sd[a-z]', 'Direct write to disk - dangerous'),
    (r'.*chown\s+-R\s+.*\s+/', 'Recursive ownership change from root'),
    (r'.*chmod\s+-R\s+777', 'Dangerous permissions - security risk'),
]


# Medium risk patterns (require approval)
MEDIUM_RISK_PATTERNS = [
    (r'systemctl\s+(restart|reload|start|stop)\s+', 'Service state change'),
    (r'podman\s+(restart|stop|start)\s+', 'Container state change'),
    (r'docker\s+(restart|stop|start)\s+', 'Container state change'),
    (r'reboot', 'System reboot'),
    (r'shutdown', 'System shutdown'),
    (r'systemctl\s+enable\s+', 'Enable service at boot'),
    (r'systemctl\s+disable\s+', 'Disable service at boot'),
]


# Read-only patterns (safe)
READONLY_PATTERNS = [
    r'^(htop|top|iotop|iftop|nethogs)(\s|$)',
    r'^(ls|cat|head|tail|less|more|grep|find)\s+',
    r'^(ps|pstree|pgrep)\s+',
    r'^(df|du|free|uptime|w|who)(\s|$)',
    r'^(netstat|ss|ip\s+(addr|route|link))\s+',
    r'^systemctl\s+(status|list-units|list-sockets|show)\s+',
    r'^journalctl\s+',
    r'^(podman|docker)\s+(ps|inspect|images|logs)\s+',
    r'^ansible-playbook\s+.*--check',
]


def assess_command_risk(command: str) -> dict:
    """
    Assess the risk level of a command.

    Uses plugin system first, falls back to pattern matching.

    Args:
        command: The command to assess

    Returns:
        Dict with risk level, category, and rationale
    """

    # Try plugin system first
    from .plugins import get_plugin_registry
    registry = get_plugin_registry()
    result = registry.find_command_spec(command)

    if result:
        plugin, spec = result
        return {
            'risk': spec.risk,
            'category': plugin.category,
            'is_readonly': spec.risk == RiskLevel.LOW and spec.level == AuthLevel.AUTO,
            'suggestion': spec.level,
            'reason': spec.rationale,
            'recommended_action': 'ADD_AUTO' if spec.level == AuthLevel.AUTO else 'ADD_MANUAL',
            'plugin': plugin.name,
            'examples': spec.examples or [],
        }

    # Check dangerous patterns first
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.match(pattern, command, re.IGNORECASE):
            return {
                'risk': RiskLevel.CRITICAL,
                'category': 'destructive',
                'is_readonly': False,
                'suggestion': AuthLevel.BLOCKED,
                'reason': reason,
                'recommended_action': 'BLOCK_PERMANENTLY'
            }

    # Check medium risk patterns
    for pattern, reason in MEDIUM_RISK_PATTERNS:
        if re.match(pattern, command, re.IGNORECASE):
            return {
                'risk': RiskLevel.MEDIUM,
                'category': 'system_modification',
                'is_readonly': False,
                'suggestion': AuthLevel.MANUAL,
                'reason': reason,
                'recommended_action': 'ADD_MANUAL'
            }

    # Check read-only patterns
    for pattern in READONLY_PATTERNS:
        if re.match(pattern, command):
            return {
                'risk': RiskLevel.LOW,
                'category': 'monitoring',
                'is_readonly': True,
                'suggestion': AuthLevel.AUTO,
                'reason': 'Read-only operation',
                'recommended_action': 'ADD_AUTO'
            }

    # Unknown command
    return {
        'risk': RiskLevel.UNKNOWN,
        'category': 'unknown',
        'is_readonly': False,
        'suggestion': None,
        'reason': 'Command not recognized - manual review required',
        'recommended_action': 'MANUAL_REVIEW'
    }


def find_similar_commands(command: str) -> list[str]:
    """
    Find similar commands in the whitelist.

    Args:
        command: The command to compare

    Returns:
        List of similar command patterns
    """
    similar = []

    # Extract base command (first word)
    base_cmd = command.split()[0] if command else ""

    for rule in COMMAND_WHITELIST:
        # Check if same base command
        if base_cmd in rule.pattern:
            similar.append(f"{rule.description} ({rule.level.value})")

        # Check if same category (monitoring, network, etc.)
        # This is a simple heuristic based on pattern keywords
        if any(keyword in rule.pattern.lower() for keyword in ['systemctl', 'journalctl', 'podman', 'ps', 'log']):
            if any(keyword in command.lower() for keyword in ['systemctl', 'journalctl', 'podman', 'ps', 'log']):
                if f"{rule.description} ({rule.level.value})" not in similar:
                    similar.append(f"{rule.description} ({rule.level.value})")

    return similar[:5]  # Limit to 5 most relevant


def analyze_command_safety(command: str) -> CommandAnalysis:
    """
    Perform comprehensive safety analysis of a command.

    Args:
        command: The command to analyze

    Returns:
        CommandAnalysis with full details
    """

    # Check plugin system first
    try:
        from .plugins import get_plugin_registry
        registry = get_plugin_registry()
        result = registry.find_command_spec(command)

        if result:
            plugin, spec = result
            return CommandAnalysis(
                command=command,
                risk_level=spec.risk,
                category=plugin.category,
                is_readonly=spec.risk == RiskLevel.LOW and spec.level == AuthLevel.AUTO,
                suggested_level=spec.level,
                suggested_ssh_user=spec.ssh_user,
                rationale=spec.rationale,
                similar_commands=[],
                can_auto_add=spec.level == AuthLevel.AUTO,
                recommended_action='ADD_AUTO' if spec.level == AuthLevel.AUTO else 'ADD_MANUAL',
            )
    except Exception:
        pass  # Fall through to pattern matching

    # Check known safe commands
    base_cmd = command.split()[0] if command else ""
    if base_cmd in KNOWN_SAFE_COMMANDS:
        info = KNOWN_SAFE_COMMANDS[base_cmd]
        return CommandAnalysis(
            command=command,
            risk_level=info['risk'],
            category=info['category'],
            is_readonly=True,
            suggested_level=info['level'],
            suggested_ssh_user=info['user'],
            rationale=info['rationale'],
            similar_commands=find_similar_commands(command),
            can_auto_add=True,
            recommended_action='ADD_AUTO'
        )

    # Assess risk
    risk_info = assess_command_risk(command)

    return CommandAnalysis(
        command=command,
        risk_level=risk_info['risk'],
        category=risk_info['category'],
        is_readonly=risk_info['is_readonly'],
        suggested_level=risk_info['suggestion'],
        suggested_ssh_user='mcp-reader' if risk_info['is_readonly'] else 'pra-runner',
        rationale=risk_info['reason'],
        similar_commands=find_similar_commands(command),
        can_auto_add=risk_info['risk'] == RiskLevel.LOW,
        recommended_action=risk_info['recommended_action']
    )
