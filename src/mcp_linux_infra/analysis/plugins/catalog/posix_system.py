"""POSIX system commands plugin - standard Unix utilities."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class PosixSystemPlugin(CommandPlugin):
    """
    POSIX standard system commands.

    Core Unix utilities for system information and control.
    """

    @property
    def name(self) -> str:
        return "posix-system"

    @property
    def category(self) -> str:
        return "posix"

    @property
    def description(self) -> str:
        return "POSIX standard system utilities (uname, uptime, hostname, etc.)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'uname': CommandSpec(
                pattern=r'^uname(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print system information',
                rationale='POSIX standard - read-only system info',
                examples=[
                    'uname -a',
                    'uname -s',
                    'uname -r',
                ],
                flags=[
                    '-a: All information',
                    '-s: Kernel name',
                    '-r: Kernel release',
                    '-m: Machine hardware',
                    '-n: Node name',
                ]
            ),

            'hostname': CommandSpec(
                pattern=r'^hostname(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show or set system hostname',
                rationale='Read-only when no args - POSIX standard',
                examples=[
                    'hostname',
                    'hostname -f',
                    'hostname -i',
                ],
                flags=[
                    '-f: FQDN',
                    '-i: IP address',
                    '-s: Short name',
                ]
            ),

            'uptime': CommandSpec(
                pattern=r'^uptime(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show system uptime',
                rationale='POSIX standard - read-only',
                examples=[
                    'uptime',
                    'uptime -p',
                    'uptime -s',
                ],
                flags=[
                    '-p: Pretty format',
                    '-s: System up since',
                ]
            ),

            'who': CommandSpec(
                pattern=r'^who(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show logged in users',
                rationale='POSIX standard - read-only',
                examples=[
                    'who',
                    'who -b',
                    'who -q',
                ],
                flags=[
                    '-b: Last system boot',
                    '-q: Quick mode',
                    '-H: Print headers',
                ]
            ),

            'w': CommandSpec(
                pattern=r'^w(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show who is logged on',
                rationale='Extended who command - read-only',
                examples=[
                    'w',
                    'w -h',
                    'w username',
                ],
                flags=[
                    '-h: No header',
                    '-s: Short format',
                    '-i: IP instead of hostname',
                ]
            ),

            'whoami': CommandSpec(
                pattern=r'^whoami$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print effective user',
                rationale='POSIX standard - read-only',
                examples=[
                    'whoami',
                ],
                flags=[]
            ),

            'id': CommandSpec(
                pattern=r'^id(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print user identity',
                rationale='POSIX standard - read-only',
                examples=[
                    'id',
                    'id username',
                    'id -u',
                ],
                flags=[
                    '-u: User ID only',
                    '-g: Group ID only',
                    '-G: All group IDs',
                    '-n: Name instead of number',
                ]
            ),

            'date': CommandSpec(
                pattern=r'^date(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print or set system date',
                rationale='Read-only when no set operation',
                examples=[
                    'date',
                    'date "+%Y-%m-%d"',
                    'date -u',
                ],
                flags=[
                    '-u: UTC time',
                    '+FORMAT: Custom format',
                    '-R: RFC 2822 format',
                    '--iso-8601: ISO format',
                ]
            ),

            'env': CommandSpec(
                pattern=r'^env(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print environment',
                rationale='POSIX standard - read-only',
                examples=[
                    'env',
                    'env | grep PATH',
                ],
                flags=[
                    '-i: Start with empty environment',
                    '-u VAR: Remove variable',
                ]
            ),

            'printenv': CommandSpec(
                pattern=r'^printenv(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print environment variables',
                rationale='Read-only environment access',
                examples=[
                    'printenv',
                    'printenv PATH',
                    'printenv HOME USER',
                ],
                flags=[]
            ),

            'echo': CommandSpec(
                pattern=r'^echo(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Display a line of text',
                rationale='POSIX standard - output only',
                examples=[
                    'echo "Hello World"',
                    'echo $PATH',
                    'echo -n "No newline"',
                ],
                flags=[
                    '-n: No trailing newline',
                    '-e: Enable backslash escapes',
                ]
            ),

            'printf': CommandSpec(
                pattern=r'^printf(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Format and print data',
                rationale='POSIX standard - output only',
                examples=[
                    'printf "Hello %s\\n" "World"',
                    'printf "%d\\n" 42',
                ],
                flags=[]
            ),

            'pwd': CommandSpec(
                pattern=r'^pwd(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print working directory',
                rationale='POSIX standard - read-only',
                examples=[
                    'pwd',
                    'pwd -P',
                ],
                flags=[
                    '-P: Physical path (no symlinks)',
                    '-L: Logical path (with symlinks)',
                ]
            ),

            'which': CommandSpec(
                pattern=r'^which(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Locate a command',
                rationale='Shows command path - read-only',
                examples=[
                    'which python',
                    'which -a python',
                ],
                flags=[
                    '-a: All matches',
                ]
            ),

            'whereis': CommandSpec(
                pattern=r'^whereis(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Locate binary, source, and manual',
                rationale='Read-only command location',
                examples=[
                    'whereis python',
                    'whereis -b python',
                ],
                flags=[
                    '-b: Binary only',
                    '-m: Manual only',
                    '-s: Source only',
                ]
            ),

            'type': CommandSpec(
                pattern=r'^type(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Display command type',
                rationale='Shell builtin - read-only',
                examples=[
                    'type ls',
                    'type -a python',
                ],
                flags=[
                    '-a: All locations',
                    '-t: Type only',
                ]
            ),

            'sleep': CommandSpec(
                pattern=r'^sleep\s+\d+(\.\d+)?[smhd]?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Delay for specified time',
                rationale='POSIX standard - harmless delay',
                examples=[
                    'sleep 5',
                    'sleep 0.5',
                    'sleep 1m',
                ],
                flags=[
                    's: seconds (default)',
                    'm: minutes',
                    'h: hours',
                    'd: days',
                ]
            ),

            'true': CommandSpec(
                pattern=r'^true$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Do nothing, successfully',
                rationale='POSIX standard - returns 0',
                examples=[
                    'true',
                ],
                flags=[]
            ),

            'false': CommandSpec(
                pattern=r'^false$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Do nothing, unsuccessfully',
                rationale='POSIX standard - returns 1',
                examples=[
                    'false',
                ],
                flags=[]
            ),

            'test': CommandSpec(
                pattern=r'^test(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Evaluate conditional expression',
                rationale='POSIX standard - read-only tests',
                examples=[
                    'test -f /etc/passwd',
                    'test -d /var/log',
                    'test "$USER" = "root"',
                ],
                flags=[
                    '-f FILE: File exists',
                    '-d DIR: Directory exists',
                    '-e PATH: Path exists',
                    '-r FILE: Readable',
                    '-w FILE: Writable',
                ]
            ),

            'basename': CommandSpec(
                pattern=r'^basename(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Strip directory and suffix',
                rationale='POSIX standard - string manipulation',
                examples=[
                    'basename /usr/bin/python',
                    'basename file.txt .txt',
                ],
                flags=[]
            ),

            'dirname': CommandSpec(
                pattern=r'^dirname(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Strip last component from path',
                rationale='POSIX standard - string manipulation',
                examples=[
                    'dirname /usr/bin/python',
                ],
                flags=[]
            ),

            'expr': CommandSpec(
                pattern=r'^expr(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Evaluate expressions',
                rationale='POSIX standard - arithmetic/string operations',
                examples=[
                    'expr 1 + 2',
                    'expr length "hello"',
                    'expr substr "hello" 1 3',
                ],
                flags=[]
            ),

            'xargs': CommandSpec(
                pattern=r'^xargs(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Build and execute command lines',
                rationale='Can execute arbitrary commands - requires approval',
                examples=[
                    'find . -name "*.txt" | xargs cat',
                    'echo file1 file2 | xargs ls -l',
                ],
                flags=[
                    '-n NUM: Max args per command',
                    '-I REPLACE: Replacement string',
                    '-P NUM: Max parallel processes',
                ]
            ),
        }
