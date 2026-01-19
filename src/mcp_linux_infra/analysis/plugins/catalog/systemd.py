"""Systemd commands plugin - service management, logs."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class SystemdPlugin(CommandPlugin):
    """
    Systemd service management and monitoring.

    Read-only commands for status/logs, write operations require approval.
    """

    @property
    def name(self) -> str:
        return "systemd"

    @property
    def category(self) -> str:
        return "systemd"

    @property
    def description(self) -> str:
        return "Systemd service management and journal logs"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'systemctl status': CommandSpec(
                pattern=r'^systemctl\s+status(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Service status',
                rationale='Read-only service state information',
                examples=[
                    'systemctl status nginx',
                    'systemctl status',
                ],
                flags=[
                    'SERVICE: Show specific service',
                    '-l: Full output',
                ]
            ),

            'systemctl list-units': CommandSpec(
                pattern=r'^systemctl\s+list-units(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List active units',
                rationale='Read-only list of systemd units',
                examples=[
                    'systemctl list-units',
                    'systemctl list-units --type=service',
                    'systemctl list-units --failed',
                ],
                flags=[
                    '--type=TYPE: Filter by type',
                    '--failed: Failed units only',
                    '--all: Include inactive',
                ]
            ),

            'systemctl list-unit-files': CommandSpec(
                pattern=r'^systemctl\s+list-unit-files(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List unit files',
                rationale='Show installed unit files and states',
                examples=[
                    'systemctl list-unit-files',
                    'systemctl list-unit-files --type=service',
                ],
                flags=[
                    '--type=TYPE: Filter by type',
                ]
            ),

            'systemctl show': CommandSpec(
                pattern=r'^systemctl\s+show(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show unit properties',
                rationale='Display detailed unit properties',
                examples=[
                    'systemctl show nginx',
                    'systemctl show -p ActiveState nginx',
                ],
                flags=[
                    '-p PROPERTY: Show specific property',
                    'SERVICE: Target service',
                ]
            ),

            'systemctl is-active': CommandSpec(
                pattern=r'^systemctl\s+is-active(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Check if service is active',
                rationale='Simple active state check',
                examples=[
                    'systemctl is-active nginx',
                ],
                flags=[]
            ),

            'systemctl is-enabled': CommandSpec(
                pattern=r'^systemctl\s+is-enabled(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Check if service is enabled',
                rationale='Simple enabled state check',
                examples=[
                    'systemctl is-enabled nginx',
                ],
                flags=[]
            ),

            'systemctl restart': CommandSpec(
                pattern=r'^systemctl\s+restart(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Restart service',
                rationale='Service restart - requires approval',
                examples=[
                    'systemctl restart nginx',
                    'systemctl restart unbound',
                ],
                flags=[]
            ),

            'systemctl reload': CommandSpec(
                pattern=r'^systemctl\s+reload(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Reload service configuration',
                rationale='Config reload - requires approval',
                examples=[
                    'systemctl reload nginx',
                    'systemctl reload caddy',
                ],
                flags=[]
            ),

            'systemctl start': CommandSpec(
                pattern=r'^systemctl\s+start(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Start service',
                rationale='Service start - requires approval',
                examples=[
                    'systemctl start nginx',
                ],
                flags=[]
            ),

            'systemctl stop': CommandSpec(
                pattern=r'^systemctl\s+stop(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Stop service',
                rationale='Service stop - requires approval',
                examples=[
                    'systemctl stop nginx',
                ],
                flags=[]
            ),

            'systemctl enable': CommandSpec(
                pattern=r'^systemctl\s+enable(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Enable service at boot',
                rationale='Persistent change - requires approval',
                examples=[
                    'systemctl enable nginx',
                ],
                flags=[
                    '--now: Also start service',
                ]
            ),

            'systemctl disable': CommandSpec(
                pattern=r'^systemctl\s+disable(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Disable service at boot',
                rationale='Persistent change - requires approval',
                examples=[
                    'systemctl disable nginx',
                ],
                flags=[
                    '--now: Also stop service',
                ]
            ),

            'journalctl': CommandSpec(
                pattern=r'^journalctl(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Query systemd journal',
                rationale='Read-only access to system logs',
                examples=[
                    'journalctl -u nginx',
                    'journalctl -u nginx -n 100',
                    'journalctl --since "1 hour ago"',
                    'journalctl -f',
                ],
                flags=[
                    '-u UNIT: Show logs for unit',
                    '-n NUM: Number of lines',
                    '-f: Follow logs',
                    '--since TIME: Time range',
                    '-p PRIORITY: Log priority',
                ]
            ),

            'systemctl cat': CommandSpec(
                pattern=r'^systemctl\s+cat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show unit file',
                rationale='Display unit file contents',
                examples=[
                    'systemctl cat nginx',
                ],
                flags=[]
            ),

            'systemctl list-dependencies': CommandSpec(
                pattern=r'^systemctl\s+list-dependencies(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show unit dependencies',
                rationale='Display dependency tree',
                examples=[
                    'systemctl list-dependencies nginx',
                ],
                flags=[
                    '--reverse: Reverse dependencies',
                ]
            ),
        }
