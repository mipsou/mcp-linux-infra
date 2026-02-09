"""POSIX text processing commands."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class PosixTextPlugin(CommandPlugin):
    """
    POSIX standard text processing utilities.
    """

    @property
    def name(self) -> str:
        return "posix-text"

    @property
    def category(self) -> str:
        return "posix"

    @property
    def description(self) -> str:
        return "POSIX text processing (sed, awk, cut, sort, etc.)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'sed': CommandSpec(
                pattern=r'^sed(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Stream editor',
                rationale='POSIX standard - text transformation',
                examples=[
                    'sed "s/old/new/g" file.txt',
                    'sed -n "10,20p" file.txt',
                    'echo "text" | sed "s/x/X/"',
                ],
                flags=[
                    '-n: Suppress output',
                    '-e SCRIPT: Add script',
                    '-i: In-place edit (CAREFUL)',
                ]
            ),

            'awk': CommandSpec(
                pattern=r'^awk(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Pattern scanning and processing',
                rationale='POSIX standard - text processing',
                examples=[
                    'awk "{print $1}" file.txt',
                    'awk -F: "{print $1}" /etc/passwd',
                    'ps aux | awk "{sum+=$3} END {print sum}"',
                ],
                flags=[
                    '-F SEP: Field separator',
                    '-v VAR=VALUE: Set variable',
                ]
            ),

            'cut': CommandSpec(
                pattern=r'^cut(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Remove sections from lines',
                rationale='POSIX standard - column extraction',
                examples=[
                    'cut -d: -f1 /etc/passwd',
                    'cut -c1-10 file.txt',
                    'echo "a:b:c" | cut -d: -f2',
                ],
                flags=[
                    '-d DELIM: Delimiter',
                    '-f FIELDS: Field numbers',
                    '-c RANGE: Character positions',
                ]
            ),

            'paste': CommandSpec(
                pattern=r'^paste(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Merge lines of files',
                rationale='POSIX standard - column joining',
                examples=[
                    'paste file1.txt file2.txt',
                    'paste -d, file1.txt file2.txt',
                ],
                flags=[
                    '-d DELIM: Delimiter',
                    '-s: Serial mode',
                ]
            ),

            'sort': CommandSpec(
                pattern=r'^sort(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Sort lines of text',
                rationale='POSIX standard - read-only sorting',
                examples=[
                    'sort file.txt',
                    'sort -n numbers.txt',
                    'sort -r file.txt',
                ],
                flags=[
                    '-n: Numeric sort',
                    '-r: Reverse',
                    '-u: Unique',
                    '-k FIELD: Sort by field',
                ]
            ),

            'uniq': CommandSpec(
                pattern=r'^uniq(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Report or omit repeated lines',
                rationale='POSIX standard - duplicate removal',
                examples=[
                    'uniq file.txt',
                    'uniq -c file.txt',
                    'sort file.txt | uniq',
                ],
                flags=[
                    '-c: Count occurrences',
                    '-d: Only duplicates',
                    '-u: Only unique',
                ]
            ),

            'tr': CommandSpec(
                pattern=r'^tr(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Translate or delete characters',
                rationale='POSIX standard - character transformation',
                examples=[
                    'echo "hello" | tr "a-z" "A-Z"',
                    'tr -d "\\n" < file.txt',
                    'tr -s " " < file.txt',
                ],
                flags=[
                    '-d SET: Delete characters',
                    '-s SET: Squeeze repeats',
                    '-c SET: Complement',
                ]
            ),

            'expand': CommandSpec(
                pattern=r'^expand(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Convert tabs to spaces',
                rationale='POSIX standard - whitespace conversion',
                examples=[
                    'expand file.txt',
                    'expand -t 4 file.txt',
                ],
                flags=[
                    '-t NUM: Tab stops',
                ]
            ),

            'unexpand': CommandSpec(
                pattern=r'^unexpand(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Convert spaces to tabs',
                rationale='POSIX standard - whitespace conversion',
                examples=[
                    'unexpand file.txt',
                    'unexpand -t 4 file.txt',
                ],
                flags=[
                    '-t NUM: Tab stops',
                    '-a: All spaces',
                ]
            ),

            'join': CommandSpec(
                pattern=r'^join(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Join lines of two files',
                rationale='POSIX standard - relational join',
                examples=[
                    'join file1.txt file2.txt',
                    'join -1 2 -2 1 file1.txt file2.txt',
                ],
                flags=[
                    '-1 FIELD: Field from file 1',
                    '-2 FIELD: Field from file 2',
                    '-t DELIM: Delimiter',
                ]
            ),

            'comm': CommandSpec(
                pattern=r'^comm(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Compare sorted files',
                rationale='POSIX standard - line comparison',
                examples=[
                    'comm file1.txt file2.txt',
                    'comm -12 file1.txt file2.txt',
                ],
                flags=[
                    '-1: Suppress column 1',
                    '-2: Suppress column 2',
                    '-3: Suppress column 3',
                ]
            ),

            'fold': CommandSpec(
                pattern=r'^fold(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Wrap lines to width',
                rationale='POSIX standard - line wrapping',
                examples=[
                    'fold file.txt',
                    'fold -w 60 file.txt',
                ],
                flags=[
                    '-w WIDTH: Line width',
                    '-s: Break at spaces',
                ]
            ),

            'fmt': CommandSpec(
                pattern=r'^fmt(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Simple text formatter',
                rationale='Text formatting - read-only',
                examples=[
                    'fmt file.txt',
                    'fmt -w 60 file.txt',
                ],
                flags=[
                    '-w WIDTH: Line width',
                ]
            ),

            'nl': CommandSpec(
                pattern=r'^nl(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Number lines',
                rationale='POSIX standard - line numbering',
                examples=[
                    'nl file.txt',
                    'nl -ba file.txt',
                ],
                flags=[
                    '-ba: Number all lines',
                    '-bt: Number non-blank',
                ]
            ),

            'od': CommandSpec(
                pattern=r'^od(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Octal dump',
                rationale='POSIX standard - binary viewing',
                examples=[
                    'od file.bin',
                    'od -x file.bin',
                    'od -c file.bin',
                ],
                flags=[
                    '-x: Hexadecimal',
                    '-c: Characters',
                    '-b: Octal bytes',
                ]
            ),

            'hexdump': CommandSpec(
                pattern=r'^hexdump(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Hexadecimal dump',
                rationale='Binary file viewing - read-only',
                examples=[
                    'hexdump file.bin',
                    'hexdump -C file.bin',
                ],
                flags=[
                    '-C: Canonical hex+ASCII',
                    '-n NUM: Length',
                ]
            ),

            'strings': CommandSpec(
                pattern=r'^strings(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Print printable strings',
                rationale='Binary file analysis - read-only',
                examples=[
                    'strings /bin/ls',
                    'strings -n 10 file.bin',
                ],
                flags=[
                    '-n NUM: Min length',
                    '-a: All file',
                ]
            ),

            'tee': CommandSpec(
                pattern=r'^tee(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Read from stdin and write to files',
                rationale='Writes to files - requires approval',
                examples=[
                    'command | tee output.txt',
                    'command | tee -a logfile.txt',
                ],
                flags=[
                    '-a: Append',
                ]
            ),

            'column': CommandSpec(
                pattern=r'^column(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Columnate lists',
                rationale='Text formatting - read-only',
                examples=[
                    'column -t file.txt',
                    'mount | column -t',
                ],
                flags=[
                    '-t: Table format',
                    '-s DELIM: Delimiter',
                ]
            ),

            'rev': CommandSpec(
                pattern=r'^rev(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Reverse lines characterwise',
                rationale='Text transformation - read-only',
                examples=[
                    'rev file.txt',
                    'echo "hello" | rev',
                ],
                flags=[]
            ),

            'tac': CommandSpec(
                pattern=r'^tac(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Reverse lines (opposite of cat)',
                rationale='Text reversal - read-only',
                examples=[
                    'tac file.txt',
                ],
                flags=[
                    '-s SEP: Separator',
                ]
            ),
        }
