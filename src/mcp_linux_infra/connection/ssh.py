"""SSH connection management avec séparation read-only / exec."""

import asyncio
from typing import Any

import asyncssh
from asyncssh import SSHClientConnection

from ..audit import Status, log_security_violation, log_ssh_command, log_ssh_connect
from ..config import CONFIG


class SSHConnectionError(Exception):
    """Erreur de connexion SSH."""

    pass


class SSHConnectionManager:
    """
    Gestionnaire de connexions SSH avec pooling.

    Séparation stricte:
    - mcp-reader : read-only (diagnostics)
    - exec-runner : exec (actions Remote Execution)
    """

    _instance: "SSHConnectionManager | None" = None
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

        # Connection pools séparés
        self._read_connections: dict[str, SSHClientConnection] = {}
        self._exec_connections: dict[str, SSHClientConnection] = {}

        # Configuration
        self._reader_key = self._load_key(CONFIG.ssh_key_path, CONFIG.key_passphrase)
        self._exec_key = self._load_key(CONFIG.exec_key_path, CONFIG.exec_key_passphrase)

        self._initialized = True

    def _load_key(self, key_path: str | None, passphrase: str | None) -> str | None:
        """Load SSH private key."""
        if not key_path:
            return None

        try:
            with open(key_path, "r") as f:
                return f.read()
        except Exception as e:
            raise SSHConnectionError(f"Failed to load SSH key {key_path}: {e}")

    async def get_read_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """
        Get read-only SSH connection (diagnostics).

        Uses mcp-reader key and user.
        """
        username = username or CONFIG.user
        key = f"{username}@{host}"

        async with self._lock:
            # Reuse existing connection
            if key in self._read_connections:
                conn = self._read_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection
            try:
                conn = await asyncssh.connect(
                    host=host,
                    username=username,
                    client_keys=[self._reader_key] if self._reader_key else None,
                    known_hosts=None,  # INSECURE: pour dev, utiliser known_hosts en prod
                    passphrase=CONFIG.key_passphrase,
                    connect_timeout=CONFIG.ssh_connection_timeout,
                    keepalive_interval=CONFIG.ssh_keepalive_interval,
                )

                self._read_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host}: {e}")

    async def get_exec_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """
        Get exec SSH connection (remote executions).

        Uses exec-runner key and exec-runner user.
        """
        username = username or CONFIG.exec_user
        key = f"{username}@{host}"

        # Security check
        if not CONFIG.exec_key_path:
            log_security_violation(
                "pra_exec_no_key",
                {"host": host, "username": username},
            )
            raise SSHConnectionError("Remote Execution exec key not configured (exec_key_path)")

        async with self._lock:
            # Reuse existing connection
            if key in self._exec_connections:
                conn = self._exec_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection
            try:
                conn = await asyncssh.connect(
                    host=host,
                    username=username,
                    client_keys=[self._exec_key] if self._exec_key else None,
                    known_hosts=None,  # INSECURE: pour dev, utiliser known_hosts en prod
                    passphrase=CONFIG.exec_key_passphrase,
                    connect_timeout=CONFIG.ssh_connection_timeout,
                    keepalive_interval=CONFIG.ssh_keepalive_interval,
                )

                self._exec_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host} for Remote Execution exec: {e}")

    async def execute_read_command(
        self, host: str, command: list[str], username: str | None = None
    ) -> tuple[int, str, str]:
        """
        Execute read-only command via mcp-reader SSH.

        Args:
            host: Target host
            command: Command as list (will be shell-joined)
            username: SSH username (default: CONFIG.user)

        Returns:
            (returncode, stdout, stderr)
        """
        username = username or CONFIG.user

        # Security check: host whitelist
        if not CONFIG.is_host_allowed(host):
            log_security_violation(
                "host_not_allowed",
                {"host": host, "command": " ".join(command)},
                host=host,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_read_connection(host, username)

        try:
            # Execute command
            result = await conn.run(" ".join(command), check=False)

            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            status = Status.SUCCESS if returncode == 0 else Status.FAILURE
            log_ssh_command(host, username, command, status, returncode, stderr if stderr else None)

            return returncode, stdout, stderr

        except Exception as e:
            log_ssh_command(host, username, command, Status.FAILURE, -1, str(e))
            raise SSHConnectionError(f"Command execution failed on {host}: {e}")

    async def execute_exec_command(
        self, host: str, action: str, username: str | None = None
    ) -> tuple[int, str, str]:
        """
        Execute remote execution via exec-runner SSH.

        IMPORTANT: Cette méthode n'exécute que des actions whitelistées
        par le wrapper exec-runner sur le système cible.

        Args:
            host: Target host
            action: remote execution name (e.g., "restart_unbound")
            username: SSH username (default: CONFIG.exec_user)

        Returns:
            (returncode, stdout, stderr)
        """
        username = username or CONFIG.exec_user

        # Security check: host whitelist
        if not CONFIG.is_host_allowed(host):
            log_security_violation(
                "host_not_allowed_pra",
                {"host": host, "action": action},
                host=host,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_exec_connection(host, username)

        try:
            # Execute via forced-command wrapper
            # Le wrapper exec-runner sur le target gère la whitelist
            result = await conn.run(action, check=False)

            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            status = Status.SUCCESS if returncode == 0 else Status.FAILURE
            log_ssh_command(host, username, [action], status, returncode, stderr if stderr else None)

            return returncode, stdout, stderr

        except Exception as e:
            log_ssh_command(host, username, [action], Status.FAILURE, -1, str(e))
            raise SSHConnectionError(f"remote execution '{action}' failed on {host}: {e}")

    async def close_all(self):
        """Close all pooled connections."""
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


# Global singleton
_manager: SSHConnectionManager | None = None


def get_ssh_manager() -> SSHConnectionManager:
    """Get or create SSH connection manager singleton."""
    global _manager
    if _manager is None:
        _manager = SSHConnectionManager()
    return _manager


async def execute_command(
    command: list[str],
    host: str | None = None,
    username: str | None = None,
) -> tuple[int, str, str]:
    """
    Execute read-only command (diagnostics).

    Local if host=None, remote via SSH mcp-reader if host specified.
    """
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
        # Remote execution via mcp-reader
        manager = get_ssh_manager()
        return await manager.execute_read_command(host, command, username)


async def execute_remote_execution(
    action: str,
    host: str,
    username: str | None = None,
) -> tuple[int, str, str]:
    """
    Execute remote execution via exec-runner SSH.

    Always remote, never local.
    """
    manager = get_ssh_manager()
    return await manager.execute_exec_command(host, action, username)
