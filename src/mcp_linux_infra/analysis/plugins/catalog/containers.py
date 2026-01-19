"""Container commands plugin - Podman and Docker."""

from ..base import CommandPlugin, CommandSpec
from ...command_analysis import RiskLevel
from ....authorization.models import AuthLevel


class ContainersPlugin(CommandPlugin):
    """
    Container management (Podman/Docker).

    Read-only commands for inspection, write operations require approval.
    """

    @property
    def name(self) -> str:
        return "containers"

    @property
    def category(self) -> str:
        return "containers"

    @property
    def description(self) -> str:
        return "Podman and Docker container management"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            # Podman read-only
            'podman ps': CommandSpec(
                pattern=r'^podman\s+ps(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List containers',
                rationale='Read-only container listing',
                examples=[
                    'podman ps',
                    'podman ps -a',
                    'podman ps --filter status=running',
                ],
                flags=[
                    '-a: All containers',
                    '--filter KEY=VALUE: Filter',
                    '-q: Quiet (IDs only)',
                ]
            ),

            'podman inspect': CommandSpec(
                pattern=r'^podman\s+inspect(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Inspect container',
                rationale='Read-only container details',
                examples=[
                    'podman inspect mycontainer',
                    'podman inspect --format "{{.State.Status}}" mycontainer',
                ],
                flags=[
                    '--format TEMPLATE: Go template',
                ]
            ),

            'podman logs': CommandSpec(
                pattern=r'^podman\s+logs(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Container logs',
                rationale='Read-only container logs',
                examples=[
                    'podman logs mycontainer',
                    'podman logs -f mycontainer',
                    'podman logs --tail 100 mycontainer',
                ],
                flags=[
                    '-f: Follow logs',
                    '--tail NUM: Last N lines',
                    '--since TIME: Time range',
                ]
            ),

            'podman images': CommandSpec(
                pattern=r'^podman\s+images(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List images',
                rationale='Read-only image listing',
                examples=[
                    'podman images',
                    'podman images -a',
                ],
                flags=[
                    '-a: All images',
                    '-q: Quiet (IDs only)',
                ]
            ),

            'podman stats': CommandSpec(
                pattern=r'^podman\s+stats(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Container resource usage',
                rationale='Read-only resource statistics',
                examples=[
                    'podman stats',
                    'podman stats mycontainer',
                    'podman stats --no-stream',
                ],
                flags=[
                    '--no-stream: One-time output',
                ]
            ),

            'podman top': CommandSpec(
                pattern=r'^podman\s+top(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Container processes',
                rationale='Read-only process listing',
                examples=[
                    'podman top mycontainer',
                ],
                flags=[]
            ),

            # Podman write operations
            'podman restart': CommandSpec(
                pattern=r'^podman\s+restart(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Restart container',
                rationale='Container restart - requires approval',
                examples=[
                    'podman restart mycontainer',
                ],
                flags=[
                    '-t TIMEOUT: Shutdown timeout',
                ]
            ),

            'podman start': CommandSpec(
                pattern=r'^podman\s+start(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Start container',
                rationale='Container start - requires approval',
                examples=[
                    'podman start mycontainer',
                ],
                flags=[]
            ),

            'podman stop': CommandSpec(
                pattern=r'^podman\s+stop(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Stop container',
                rationale='Container stop - requires approval',
                examples=[
                    'podman stop mycontainer',
                ],
                flags=[
                    '-t TIMEOUT: Shutdown timeout',
                ]
            ),

            'podman rm': CommandSpec(
                pattern=r'^podman\s+rm(\s+.*)?$',
                risk=RiskLevel.HIGH,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Remove container',
                rationale='Destructive operation - requires approval',
                examples=[
                    'podman rm mycontainer',
                ],
                flags=[
                    '-f: Force remove',
                ]
            ),

            # Docker equivalents (read-only)
            'docker ps': CommandSpec(
                pattern=r'^docker\s+ps(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List containers',
                rationale='Read-only container listing',
                examples=[
                    'docker ps',
                    'docker ps -a',
                ],
                flags=[
                    '-a: All containers',
                    '-q: Quiet (IDs only)',
                ]
            ),

            'docker inspect': CommandSpec(
                pattern=r'^docker\s+inspect(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Inspect container',
                rationale='Read-only container details',
                examples=[
                    'docker inspect mycontainer',
                ],
                flags=[]
            ),

            'docker logs': CommandSpec(
                pattern=r'^docker\s+logs(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Container logs',
                rationale='Read-only container logs',
                examples=[
                    'docker logs mycontainer',
                    'docker logs -f mycontainer',
                ],
                flags=[
                    '-f: Follow logs',
                    '--tail NUM: Last N lines',
                ]
            ),

            'docker images': CommandSpec(
                pattern=r'^docker\s+images(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='List images',
                rationale='Read-only image listing',
                examples=[
                    'docker images',
                ],
                flags=[
                    '-a: All images',
                ]
            ),

            'docker stats': CommandSpec(
                pattern=r'^docker\s+stats(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthLevel.AUTO,
                ssh_user='mcp-reader',
                description='Container resource usage',
                rationale='Read-only resource statistics',
                examples=[
                    'docker stats',
                    'docker stats --no-stream',
                ],
                flags=[
                    '--no-stream: One-time output',
                ]
            ),

            # Docker write operations
            'docker restart': CommandSpec(
                pattern=r'^docker\s+restart(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Restart container',
                rationale='Container restart - requires approval',
                examples=[
                    'docker restart mycontainer',
                ],
                flags=[]
            ),

            'docker start': CommandSpec(
                pattern=r'^docker\s+start(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Start container',
                rationale='Container start - requires approval',
                examples=[
                    'docker start mycontainer',
                ],
                flags=[]
            ),

            'docker stop': CommandSpec(
                pattern=r'^docker\s+stop(\s+.*)?$',
                risk=RiskLevel.MEDIUM,
                level=AuthLevel.MANUAL,
                ssh_user='pra-runner',
                description='Stop container',
                rationale='Container stop - requires approval',
                examples=[
                    'docker stop mycontainer',
                ],
                flags=[]
            ),
        }
