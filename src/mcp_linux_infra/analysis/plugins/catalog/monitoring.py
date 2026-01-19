"""Monitoring commands plugin - process, CPU, memory, I/O monitoring."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class MonitoringPlugin(CommandPlugin):
    """
    Process and system monitoring commands.

    All commands are read-only and safe for continuous observation.
    """

    @property
    def name(self) -> str:
        return "monitoring"

    @property
    def category(self) -> str:
        return "monitoring"

    @property
    def description(self) -> str:
        return "Process, CPU, memory, and I/O monitoring tools (read-only)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'htop': CommandSpec(
                pattern=r'^htop(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Interactive process viewer',
                rationale='Read-only process monitoring with CPU/memory stats',
                examples=[
                    'htop',
                    'htop -u www-data',
                    'htop -p 1234',
                ],
                flags=[
                    '-u USER: Filter by user',
                    '-p PID: Show specific process',
                    '-t: Tree view',
                ]
            ),

            'top': CommandSpec(
                pattern=r'^top(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Process monitor',
                rationale='Standard read-only process viewer',
                examples=[
                    'top',
                    'top -b -n 1',
                    'top -u nginx',
                ],
                flags=[
                    '-b: Batch mode',
                    '-n NUM: Number of iterations',
                    '-u USER: Filter by user',
                ]
            ),

            'iotop': CommandSpec(
                pattern=r'^iotop(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='I/O monitoring by process',
                rationale='Read-only disk I/O monitoring',
                examples=[
                    'iotop',
                    'iotop -b -n 1',
                    'iotop -o',
                ],
                flags=[
                    '-b: Batch mode',
                    '-n NUM: Iterations',
                    '-o: Only show processes doing I/O',
                ]
            ),

            'iftop': CommandSpec(
                pattern=r'^iftop(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network bandwidth monitor',
                rationale='Read-only network interface traffic monitoring',
                examples=[
                    'iftop',
                    'iftop -i eth0',
                    'iftop -n',
                ],
                flags=[
                    '-i IFACE: Monitor specific interface',
                    '-n: No DNS resolution',
                    '-B: Display in bytes',
                ]
            ),

            'nethogs': CommandSpec(
                pattern=r'^nethogs(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network traffic monitor per process',
                rationale='Read-only per-process network bandwidth monitoring',
                examples=[
                    'nethogs',
                    'nethogs eth0',
                    'nethogs -d 5',
                ],
                flags=[
                    '-d DELAY: Refresh delay',
                    'INTERFACE: Monitor specific interface',
                ]
            ),

            'atop': CommandSpec(
                pattern=r'^atop(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Advanced system monitor',
                rationale='Read-only comprehensive system and process monitoring',
                examples=[
                    'atop',
                    'atop -m',
                    'atop 5',
                ],
                flags=[
                    '-m: Memory view',
                    '-d: Disk view',
                    '-n: Network view',
                ]
            ),

            'vmstat': CommandSpec(
                pattern=r'^vmstat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Virtual memory statistics',
                rationale='Read-only memory, swap, and CPU stats',
                examples=[
                    'vmstat',
                    'vmstat 1 10',
                    'vmstat -s',
                ],
                flags=[
                    'DELAY COUNT: Refresh interval and count',
                    '-s: Summary statistics',
                    '-d: Disk statistics',
                ]
            ),

            'iostat': CommandSpec(
                pattern=r'^iostat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='I/O statistics',
                rationale='Read-only CPU and I/O device statistics',
                examples=[
                    'iostat',
                    'iostat -x 1',
                    'iostat -p sda',
                ],
                flags=[
                    '-x: Extended stats',
                    '-p DEVICE: Per-partition stats',
                    'INTERVAL: Refresh interval',
                ]
            ),

            'mpstat': CommandSpec(
                pattern=r'^mpstat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Per-CPU statistics',
                rationale='Read-only per-processor statistics',
                examples=[
                    'mpstat',
                    'mpstat -P ALL',
                    'mpstat 1 5',
                ],
                flags=[
                    '-P ALL: All CPUs',
                    '-P NUM: Specific CPU',
                    'INTERVAL COUNT: Refresh settings',
                ]
            ),

            'glances': CommandSpec(
                pattern=r'^glances(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='All-in-one system monitor',
                rationale='Read-only comprehensive monitoring dashboard',
                examples=[
                    'glances',
                    'glances -1',
                    'glances --disable-network',
                ],
                flags=[
                    '-1: Per-CPU stats',
                    '--disable-PLUGIN: Disable specific plugin',
                    '-t DELAY: Refresh delay',
                ]
            ),
        }
