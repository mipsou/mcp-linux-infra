"""POSIX process management commands."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class PosixProcessPlugin(CommandPlugin):
    """
    POSIX standard process management commands.
    """

    @property
    def name(self) -> str:
        return "posix-process"

    @property
    def category(self) -> str:
        return "posix"

    @property
    def description(self) -> str:
        return "POSIX process management (ps, kill, jobs, etc.)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'ps': CommandSpec(
                pattern=r'^ps(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Process status',
                rationale='POSIX standard - read-only process listing',
                examples=[
                    'ps',
                    'ps aux',
                    'ps -ef',
                    'ps -p 1234',
                ],
                flags=[
                    'aux: All processes (BSD style)',
                    '-ef: All processes (POSIX style)',
                    '-p PID: Specific process',
                    '-u USER: User processes',
                ]
            ),

            'pgrep': CommandSpec(
                pattern=r'^pgrep(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Find processes by name',
                rationale='Read-only process search',
                examples=[
                    'pgrep nginx',
                    'pgrep -u www-data',
                    'pgrep -l python',
                ],
                flags=[
                    '-l: List name',
                    '-u USER: By user',
                    '-f: Full command line',
                    '-x: Exact match',
                ]
            ),

            'pstree': CommandSpec(
                pattern=r'^pstree(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Process tree',
                rationale='Read-only process hierarchy',
                examples=[
                    'pstree',
                    'pstree -p',
                    'pstree 1',
                ],
                flags=[
                    '-p: Show PIDs',
                    '-u: Show users',
                    '-a: Show arguments',
                ]
            ),

            'pidof': CommandSpec(
                pattern=r'^pidof(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Find process ID by name',
                rationale='Read-only PID lookup',
                examples=[
                    'pidof nginx',
                    'pidof sshd',
                ],
                flags=[
                    '-s: Single PID only',
                    '-x: Include scripts',
                ]
            ),

            'kill': CommandSpec(
                pattern=r'^kill(\s+.*)?$',
                risk=RiskLevel.HIGH,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Send signal to process',
                rationale='Can terminate processes - requires approval',
                examples=[
                    'kill 1234',
                    'kill -9 1234',
                    'kill -TERM 1234',
                ],
                flags=[
                    '-SIGNAL: Specify signal',
                    '-9: SIGKILL (force)',
                    '-15: SIGTERM (graceful)',
                    '-HUP: SIGHUP (reload)',
                ]
            ),

            'killall': CommandSpec(
                pattern=r'^killall(\s+.*)?$',
                risk=RiskLevel.HIGH,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Kill processes by name',
                rationale='Mass termination - requires approval',
                examples=[
                    'killall nginx',
                    'killall -9 python',
                ],
                flags=[
                    '-SIGNAL: Specify signal',
                    '-9: SIGKILL',
                    '-u USER: By user',
                ]
            ),

            'pkill': CommandSpec(
                pattern=r'^pkill(\s+.*)?$',
                risk=RiskLevel.HIGH,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Signal processes by name',
                rationale='Can terminate processes - requires approval',
                examples=[
                    'pkill nginx',
                    'pkill -9 python',
                    'pkill -u www-data',
                ],
                flags=[
                    '-SIGNAL: Specify signal',
                    '-u USER: By user',
                    '-f: Match full command',
                ]
            ),

            'nice': CommandSpec(
                pattern=r'^nice(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Run program with modified priority',
                rationale='Changes scheduling priority - requires approval',
                examples=[
                    'nice -n 10 command',
                    'nice command',
                ],
                flags=[
                    '-n NUM: Priority adjustment',
                ]
            ),

            'renice': CommandSpec(
                pattern=r'^renice(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Alter priority of running process',
                rationale='Changes process priority - requires approval',
                examples=[
                    'renice +5 -p 1234',
                    'renice 10 -u www-data',
                ],
                flags=[
                    '-p PID: By process ID',
                    '-u USER: By user',
                    '-g GROUP: By group',
                ]
            ),

            'nohup': CommandSpec(
                pattern=r'^nohup(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Run command immune to hangups',
                rationale='Starts background process - requires approval',
                examples=[
                    'nohup command &',
                    'nohup ./script.sh &',
                ],
                flags=[]
            ),

            'timeout': CommandSpec(
                pattern=r'^timeout(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Run command with time limit',
                rationale='Safe wrapper - read-only by default',
                examples=[
                    'timeout 10s command',
                    'timeout 1m ping google.com',
                ],
                flags=[
                    '-s SIGNAL: Send signal on timeout',
                    '-k DURATION: Kill after duration',
                ]
            ),

            'time': CommandSpec(
                pattern=r'^time(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Time command execution',
                rationale='Measurement wrapper - read-only',
                examples=[
                    'time ls -R',
                    'time sleep 5',
                ],
                flags=[
                    '-p: POSIX format',
                ]
            ),

            'watch': CommandSpec(
                pattern=r'^watch(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Execute program periodically',
                rationale='Monitoring wrapper - read-only',
                examples=[
                    'watch -n 5 uptime',
                    'watch "df -h"',
                ],
                flags=[
                    '-n SECONDS: Interval',
                    '-d: Highlight differences',
                ]
            ),

            'strace': CommandSpec(
                pattern=r'^strace(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Trace system calls',
                rationale='Debugging tool - may impact performance',
                examples=[
                    'strace ls',
                    'strace -p 1234',
                    'strace -c command',
                ],
                flags=[
                    '-p PID: Attach to process',
                    '-c: Count calls',
                    '-e SYSCALL: Filter syscalls',
                ]
            ),

            'lsof': CommandSpec(
                pattern=r'^lsof(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List open files',
                rationale='Read-only file and process info',
                examples=[
                    'lsof',
                    'lsof -i :80',
                    'lsof -u www-data',
                ],
                flags=[
                    '-i: Network files',
                    '-u USER: By user',
                    '-p PID: By process',
                    '-c NAME: By command',
                ]
            ),

            'fuser': CommandSpec(
                pattern=r'^fuser(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Identify processes using files',
                rationale='Read-only file usage info',
                examples=[
                    'fuser /var/log/syslog',
                    'fuser -v /usr/bin/python',
                ],
                flags=[
                    '-v: Verbose',
                    '-m: All files on filesystem',
                    '-k: Kill processes (DANGEROUS)',
                ]
            ),
        }
