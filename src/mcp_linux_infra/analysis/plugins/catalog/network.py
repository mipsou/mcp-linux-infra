"""Network commands plugin - connectivity, routing, DNS."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class NetworkPlugin(CommandPlugin):
    """
    Network diagnostic and monitoring commands.

    All commands are read-only network tools for diagnostics.
    """

    @property
    def name(self) -> str:
        return "network"

    @property
    def category(self) -> str:
        return "network"

    @property
    def description(self) -> str:
        return "Network connectivity, routing, and diagnostic tools (read-only)"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'ping': CommandSpec(
                pattern=r'^ping(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network connectivity test',
                rationale='ICMP echo test for network reachability',
                examples=[
                    'ping google.com',
                    'ping -c 4 8.8.8.8',
                    'ping -I eth0 192.168.1.1',
                ],
                flags=[
                    '-c COUNT: Number of packets',
                    '-i INTERVAL: Packet interval',
                    '-I INTERFACE: Source interface',
                ]
            ),

            'traceroute': CommandSpec(
                pattern=r'^traceroute(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network path tracing',
                rationale='Trace network hops to destination',
                examples=[
                    'traceroute google.com',
                    'traceroute -n 8.8.8.8',
                    'traceroute -m 20 example.com',
                ],
                flags=[
                    '-n: No DNS resolution',
                    '-m TTL: Max hops',
                    '-w TIMEOUT: Wait timeout',
                ]
            ),

            'netstat': CommandSpec(
                pattern=r'^netstat(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network connections status',
                rationale='Display active network connections and routing',
                examples=[
                    'netstat -tuln',
                    'netstat -anp',
                    'netstat -r',
                ],
                flags=[
                    '-t: TCP connections',
                    '-u: UDP connections',
                    '-l: Listening sockets',
                    '-n: Numeric addresses',
                    '-p: Process information',
                    '-r: Routing table',
                ]
            ),

            'ss': CommandSpec(
                pattern=r'^ss(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Socket statistics',
                rationale='Modern alternative to netstat for socket info',
                examples=[
                    'ss -tuln',
                    'ss -anp',
                    'ss -s',
                ],
                flags=[
                    '-t: TCP sockets',
                    '-u: UDP sockets',
                    '-l: Listening sockets',
                    '-n: Numeric',
                    '-p: Process info',
                    '-s: Summary statistics',
                ]
            ),

            'ip addr': CommandSpec(
                pattern=r'^ip\s+addr(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show IP addresses',
                rationale='Display interface IP configuration',
                examples=[
                    'ip addr',
                    'ip addr show eth0',
                    'ip -4 addr',
                ],
                flags=[
                    'show IFACE: Specific interface',
                    '-4: IPv4 only',
                    '-6: IPv6 only',
                ]
            ),

            'ip route': CommandSpec(
                pattern=r'^ip\s+route(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show routing table',
                rationale='Display kernel routing table',
                examples=[
                    'ip route',
                    'ip route show',
                    'ip route get 8.8.8.8',
                ],
                flags=[
                    'show: Display routes',
                    'get ADDR: Route to address',
                ]
            ),

            'ip link': CommandSpec(
                pattern=r'^ip\s+link(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Show network interfaces',
                rationale='Display link-layer interface status',
                examples=[
                    'ip link',
                    'ip link show eth0',
                ],
                flags=[
                    'show IFACE: Specific interface',
                ]
            ),

            'dig': CommandSpec(
                pattern=r'^dig(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='DNS lookup',
                rationale='Query DNS servers for domain information',
                examples=[
                    'dig google.com',
                    'dig @8.8.8.8 example.com',
                    'dig +short example.com',
                ],
                flags=[
                    '@SERVER: Query specific DNS server',
                    '+short: Short output',
                    'TYPE: Record type (A, MX, NS, etc.)',
                ]
            ),

            'nslookup': CommandSpec(
                pattern=r'^nslookup(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='DNS query',
                rationale='Interactive DNS lookup tool',
                examples=[
                    'nslookup google.com',
                    'nslookup example.com 8.8.8.8',
                ],
                flags=[]
            ),

            'host': CommandSpec(
                pattern=r'^host(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='DNS lookup utility',
                rationale='Simple DNS lookup tool',
                examples=[
                    'host google.com',
                    'host -t MX example.com',
                ],
                flags=[
                    '-t TYPE: Record type',
                    '-v: Verbose output',
                ]
            ),

            'curl': CommandSpec(
                pattern=r'^curl(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='HTTP client',
                rationale='Fetch URLs and test HTTP endpoints',
                examples=[
                    'curl https://example.com',
                    'curl -I https://example.com',
                    'curl -s https://api.example.com/health',
                ],
                flags=[
                    '-I: HEAD request only',
                    '-s: Silent mode',
                    '-v: Verbose',
                    '-H: Custom header',
                ]
            ),

            'wget': CommandSpec(
                pattern=r'^wget(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Download files',
                rationale='Downloads files to disk - requires approval',
                examples=[
                    'wget https://example.com/file.txt',
                    'wget -O /tmp/test.txt https://example.com/file.txt',
                ],
                flags=[
                    '-O FILE: Output file',
                    '--spider: Check only',
                    '-q: Quiet mode',
                ]
            ),

            'mtr': CommandSpec(
                pattern=r'^mtr(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Network diagnostic tool',
                rationale='Combined traceroute and ping',
                examples=[
                    'mtr google.com',
                    'mtr -n 8.8.8.8',
                    'mtr -r -c 10 example.com',
                ],
                flags=[
                    '-n: No DNS',
                    '-r: Report mode',
                    '-c COUNT: Ping count',
                ]
            ),

            'tcpdump': CommandSpec(
                pattern=r'^tcpdump(\s+.*)?$',
                risk=RiskLevel.HIGH,
                level=AuthLevel.MANUAL,
                ssh_user='exec-runner',
                description='Packet capture',
                rationale='Captures network packets - security sensitive',
                examples=[
                    'tcpdump -i eth0',
                    'tcpdump -n port 80',
                    'tcpdump -c 100 -w /tmp/capture.pcap',
                ],
                flags=[
                    '-i IFACE: Interface',
                    '-n: No DNS',
                    '-c COUNT: Packet count',
                    '-w FILE: Write to file',
                ]
            ),
        }
