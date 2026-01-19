"""Filesystem commands plugin - file operations, search, viewing."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class FilesystemPlugin(CommandPlugin):
    """
    Filesystem read operations.

    All commands are read-only file viewing and searching tools.
    """

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "File viewing, search, and listing tools (read-only)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'ls': CommandSpec(
                pattern=r'^ls(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List directory contents',
                rationale='Read-only directory listing',
                examples=[
                    'ls -la',
                    'ls -lh /var/log',
                    'ls -lt',
                ],
                flags=[
                    '-l: Long format',
                    '-a: Show hidden files',
                    '-h: Human-readable sizes',
                    '-t: Sort by time',
                    '-R: Recursive',
                ]
            ),

            'cat': CommandSpec(
                pattern=r'^cat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Concatenate and display files',
                rationale='Read file contents',
                examples=[
                    'cat /etc/hostname',
                    'cat file1.txt file2.txt',
                ],
                flags=[
                    '-n: Number lines',
                    '-b: Number non-blank lines',
                ]
            ),

            'head': CommandSpec(
                pattern=r'^head(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show file beginning',
                rationale='Read first lines of files',
                examples=[
                    'head /var/log/syslog',
                    'head -n 20 file.txt',
                ],
                flags=[
                    '-n NUM: Number of lines',
                    '-c NUM: Number of bytes',
                ]
            ),

            'tail': CommandSpec(
                pattern=r'^tail(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show file end',
                rationale='Read last lines of files',
                examples=[
                    'tail /var/log/syslog',
                    'tail -n 50 file.txt',
                    'tail -f /var/log/app.log',
                ],
                flags=[
                    '-n NUM: Number of lines',
                    '-f: Follow (real-time)',
                    '-F: Follow with retry',
                ]
            ),

            'less': CommandSpec(
                pattern=r'^less(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='File viewer',
                rationale='Interactive file paging',
                examples=[
                    'less /var/log/syslog',
                    'less +F file.txt',
                ],
                flags=[
                    '+F: Follow mode',
                    '-N: Line numbers',
                    '-S: No line wrap',
                ]
            ),

            'more': CommandSpec(
                pattern=r'^more(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='File pager',
                rationale='Simple file viewing',
                examples=[
                    'more /etc/hosts',
                ],
                flags=[]
            ),

            'grep': CommandSpec(
                pattern=r'^grep(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Text search',
                rationale='Pattern matching in files',
                examples=[
                    'grep error /var/log/syslog',
                    'grep -r "pattern" /etc/',
                    'grep -i ERROR file.txt',
                ],
                flags=[
                    '-i: Case insensitive',
                    '-r: Recursive',
                    '-n: Line numbers',
                    '-v: Invert match',
                    '-c: Count matches',
                ]
            ),

            'find': CommandSpec(
                pattern=r'^find(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Search for files',
                rationale='Locate files by name, size, date',
                examples=[
                    'find /var/log -name "*.log"',
                    'find . -type f -mtime -7',
                    'find /tmp -size +100M',
                ],
                flags=[
                    '-name PATTERN: Name pattern',
                    '-type TYPE: File type (f/d)',
                    '-size SIZE: File size',
                    '-mtime DAYS: Modified time',
                ]
            ),

            'du': CommandSpec(
                pattern=r'^du(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Disk usage',
                rationale='Calculate directory sizes',
                examples=[
                    'du -sh /var/log',
                    'du -h --max-depth=1',
                ],
                flags=[
                    '-s: Summary',
                    '-h: Human-readable',
                    '--max-depth=N: Depth limit',
                ]
            ),

            'df': CommandSpec(
                pattern=r'^df(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Disk space',
                rationale='Show filesystem space usage',
                examples=[
                    'df -h',
                    'df -i',
                    'df -T',
                ],
                flags=[
                    '-h: Human-readable',
                    '-i: Inodes',
                    '-T: Filesystem type',
                ]
            ),

            'file': CommandSpec(
                pattern=r'^file(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Determine file type',
                rationale='Identify file types',
                examples=[
                    'file /bin/bash',
                    'file *',
                ],
                flags=[
                    '-b: Brief mode',
                    '-i: MIME type',
                ]
            ),

            'stat': CommandSpec(
                pattern=r'^stat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='File status',
                rationale='Display detailed file information',
                examples=[
                    'stat /etc/passwd',
                    'stat -c "%n %s" file.txt',
                ],
                flags=[
                    '-c FORMAT: Custom format',
                    '-f: Filesystem info',
                ]
            ),

            'tree': CommandSpec(
                pattern=r'^tree(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Directory tree',
                rationale='Display directory structure',
                examples=[
                    'tree /etc/nginx',
                    'tree -L 2',
                    'tree -d',
                ],
                flags=[
                    '-L LEVEL: Max depth',
                    '-d: Directories only',
                    '-h: Human-readable sizes',
                ]
            ),

            'wc': CommandSpec(
                pattern=r'^wc(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Word count',
                rationale='Count lines, words, bytes',
                examples=[
                    'wc file.txt',
                    'wc -l /var/log/syslog',
                ],
                flags=[
                    '-l: Lines only',
                    '-w: Words only',
                    '-c: Bytes only',
                ]
            ),

            'diff': CommandSpec(
                pattern=r'^diff(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Compare files',
                rationale='Show differences between files',
                examples=[
                    'diff file1.txt file2.txt',
                    'diff -u old.conf new.conf',
                ],
                flags=[
                    '-u: Unified format',
                    '-c: Context format',
                    '-r: Recursive',
                ]
            ),

            'md5sum': CommandSpec(
                pattern=r'^md5sum(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='MD5 checksum',
                rationale='Calculate file checksums',
                examples=[
                    'md5sum file.txt',
                    'md5sum -c checksums.md5',
                ],
                flags=[
                    '-c FILE: Check checksums',
                ]
            ),

            'sha256sum': CommandSpec(
                pattern=r'^sha256sum(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='SHA256 checksum',
                rationale='Calculate file checksums',
                examples=[
                    'sha256sum file.txt',
                    'sha256sum -c checksums.sha256',
                ],
                flags=[
                    '-c FILE: Check checksums',
                ]
            ),
        }
