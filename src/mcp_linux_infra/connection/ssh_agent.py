"""SSH Agent integration pour sécurité maximale.

Au lieu de charger les clés SSH directement en mémoire,
on utilise SSH Agent qui:
1. Garde les clés privées hors du processus MCP
2. Signe les requêtes SSH sans exposer la clé
3. Permet révocation instantanée (ssh-add -D)
4. Compatible avec hardware tokens (YubiKey, etc.)
"""

import asyncio
import os
from pathlib import Path

import asyncssh
from asyncssh import SSHClientConnection

from ..audit import Status, log_security_violation, log_ssh_command, log_ssh_connect
from ..config import CONFIG


class SSHAgentConnectionManager:
    """
    Gestionnaire SSH utilisant SSH Agent pour sécurité maximale.

    Avantages vs clés directes:
    - Clés privées JAMAIS en mémoire du process MCP
    - IA ne peut jamais accéder aux clés
    - Support hardware tokens (YubiKey, FIDO2)
    - Révocation instantanée (ssh-add -D)
    - Audit via SSH Agent
    """

    _instance: "SSHAgentConnectionManager | None" = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize connection pools."""
        if self._initialized:
            return

        # Connection pools séparés (read-only et exec)
        self._read_connections: dict[str, SSHClientConnection] = {}
        self._exec_connections: dict[str, SSHClientConnection] = {}

        # Vérifier SSH Agent est disponible
        self._agent_available = self._check_agent()

        self._initialized = True

    def _check_agent(self) -> bool:
        """Vérifier que SSH Agent est accessible."""
        # Windows: Pageant ou OpenSSH Agent
        # Linux: SSH_AUTH_SOCK

        if os.name == "nt":
            # Windows: vérifier OpenSSH Agent service ou Pageant
            # Pageant: détection via named pipe
            # OpenSSH Agent: SSH_AUTH_SOCK ou service Windows
            return os.environ.get("SSH_AUTH_SOCK") is not None or self._check_pageant()
        else:
            # Linux/Mac: SSH_AUTH_SOCK
            auth_sock = os.environ.get("SSH_AUTH_SOCK")
            if auth_sock and Path(auth_sock).exists():
                return True
            return False

    def _check_pageant(self) -> bool:
        """Check if Pageant is running (Windows)."""
        try:
            import win32api
            import win32con

            # Try to open Pageant window
            hwnd = win32api.FindWindow("Pageant", "Pageant")
            return hwnd != 0
        except Exception:
            return False

    async def get_read_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """
        Get read-only SSH connection via Agent (mcp-reader key).

        SÉCURITÉ:
        - Clé mcp-reader.key doit être chargée dans SSH Agent
        - Commande: ssh-add /path/to/mcp-reader.key
        - Vérification: ssh-add -l
        """
        if not self._agent_available:
            raise SSHConnectionError(
                "SSH Agent not available. "
                "Please start SSH Agent and load keys with: ssh-add /path/to/key"
            )

        username = username or CONFIG.user
        key = f"{username}@{host}"

        async with self._lock:
            # Reuse existing connection
            if key in self._read_connections:
                conn = self._read_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection via SSH Agent
            try:
                conn = await asyncssh.connect(
                    host=host,
                    username=username,
                    agent_path=os.environ.get("SSH_AUTH_SOCK"),  # Use agent
                    client_keys=None,  # Pas de clé directe - agent only
                    known_hosts=None,  # TODO: activer en prod
                    connect_timeout=CONFIG.ssh_connection_timeout,
                    keepalive_interval=CONFIG.ssh_keepalive_interval,
                )

                self._read_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except asyncssh.misc.ChannelOpenError as e:
                if "agent" in str(e).lower():
                    log_security_violation(
                        "ssh_agent_key_missing",
                        {
                            "host": host,
                            "username": username,
                            "error": "mcp-reader key not loaded in SSH Agent",
                            "solution": f"Run: ssh-add {CONFIG.ssh_key_path}",
                        },
                        host=host,
                    )
                    raise SSHConnectionError(
                        f"mcp-reader key not found in SSH Agent. "
                        f"Load it with: ssh-add {CONFIG.ssh_key_path or '/path/to/mcp-reader.key'}"
                    )
                raise

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host}: {e}")

    async def get_exec_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """
        Get exec SSH connection via Agent (exec-runner key).

        SÉCURITÉ:
        - Clé exec-runner.key doit être chargée dans SSH Agent
        - Séparation stricte: clé différente de mcp-reader
        """
        if not self._agent_available:
            raise SSHConnectionError(
                "SSH Agent not available. Required for remote executions."
            )

        username = username or CONFIG.exec_user
        key = f"{username}@{host}"

        async with self._lock:
            # Reuse existing connection
            if key in self._exec_connections:
                conn = self._exec_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection via SSH Agent
            try:
                conn = await asyncssh.connect(
                    host=host,
                    username=username,
                    agent_path=os.environ.get("SSH_AUTH_SOCK"),  # Use agent
                    client_keys=None,  # Agent only
                    known_hosts=None,  # TODO: activer en prod
                    connect_timeout=CONFIG.ssh_connection_timeout,
                    keepalive_interval=CONFIG.ssh_keepalive_interval,
                )

                self._exec_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except asyncssh.misc.ChannelOpenError as e:
                if "agent" in str(e).lower():
                    log_security_violation(
                        "ssh_agent_pra_key_missing",
                        {
                            "host": host,
                            "username": username,
                            "error": "exec-runner key not loaded in SSH Agent",
                            "solution": f"Run: ssh-add {CONFIG.exec_key_path}",
                        },
                        host=host,
                    )
                    raise SSHConnectionError(
                        f"exec-runner key not found in SSH Agent. "
                        f"Load it with: ssh-add {CONFIG.exec_key_path or '/path/to/exec-runner.key'}"
                    )
                raise

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host} for Remote Execution: {e}")

    async def execute_read_command(
        self, host: str, command: list[str], username: str | None = None
    ) -> tuple[int, str, str]:
        """Execute read-only command via SSH Agent."""
        username = username or CONFIG.user

        # Security: host whitelist
        if not CONFIG.is_host_allowed(host):
            log_security_violation(
                "host_not_allowed",
                {"host": host, "command": " ".join(command)},
                host=host,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_read_connection(host, username)

        try:
            result = await conn.run(" ".join(command), check=False)

            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            status = Status.SUCCESS if returncode == 0 else Status.FAILURE
            log_ssh_command(
                host, username, command, status, returncode, stderr if stderr else None
            )

            return returncode, stdout, stderr

        except Exception as e:
            log_ssh_command(host, username, command, Status.FAILURE, -1, str(e))
            raise SSHConnectionError(f"Command execution failed on {host}: {e}")

    async def execute_exec_command(
        self, host: str, action: str, username: str | None = None
    ) -> tuple[int, str, str]:
        """Execute remote execution via SSH Agent."""
        username = username or CONFIG.exec_user

        # Security: host whitelist
        if not CONFIG.is_host_allowed(host):
            log_security_violation(
                "host_not_allowed_pra",
                {"host": host, "action": action},
                host=host,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_exec_connection(host, username)

        try:
            result = await conn.run(action, check=False)

            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            status = Status.SUCCESS if returncode == 0 else Status.FAILURE
            log_ssh_command(
                host, username, [action], status, returncode, stderr if stderr else None
            )

            return returncode, stdout, stderr

        except Exception as e:
            log_ssh_command(host, username, [action], Status.FAILURE, -1, str(e))
            raise SSHConnectionError(f"remote execution '{action}' failed on {host}: {e}")

    async def close_all(self):
        """Close all connections."""
        async with self._lock:
            for conn in list(self._read_connections.values()):
                if not conn.is_closed():
                    conn.close()
            self._read_connections.clear()

            for conn in list(self._exec_connections.values()):
                if not conn.is_closed():
                    conn.close()
            self._exec_connections.clear()

    async def cleanup_closed(self):
        """Remove closed connections from pools."""
        async with self._lock:
            self._read_connections = {
                k: v for k, v in self._read_connections.items() if not v.is_closed()
            }
            self._exec_connections = {
                k: v for k, v in self._exec_connections.items() if not v.is_closed()
            }


class SSHConnectionError(Exception):
    """SSH connection error."""

    pass


# Global singleton
_agent_manager: SSHAgentConnectionManager | None = None


def get_ssh_agent_manager() -> SSHAgentConnectionManager:
    """Get SSH Agent connection manager."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = SSHAgentConnectionManager()
    return _agent_manager


async def execute_command_via_agent(
    command: list[str],
    host: str | None = None,
    username: str | None = None,
) -> tuple[int, str, str]:
    """Execute command via SSH Agent (diagnostics)."""
    if host is None:
        # Local execution
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
        )
    else:
        # Remote via SSH Agent
        manager = get_ssh_agent_manager()
        return await manager.execute_read_command(host, command, username)


async def execute_remote_execution_via_agent(
    action: str,
    host: str,
    username: str | None = None,
) -> tuple[int, str, str]:
    """Execute remote execution via SSH Agent."""
    manager = get_ssh_agent_manager()
    return await manager.execute_exec_command(host, action, username)
