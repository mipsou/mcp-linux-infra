"""
Smart SSH Connection Manager avec fallback automatique.

Hiérarchie de sécurité:
1. SSH Agent (PRÉFÉRÉ) - sécurité maximale
2. Clés directes (FALLBACK) - avec warning
3. Échec (ERROR) - pas de clé disponible
"""

import asyncio
import os
from enum import Enum
from pathlib import Path

import asyncssh
from asyncssh import SSHClientConnection

from ..audit import EventType, LogLevel, Status, audit, log_ssh_connect
from ..config import CONFIG


class SSHAuthMode(str, Enum):
    """Mode d'authentification SSH utilisé."""

    AGENT = "agent"  # Via SSH Agent (sécurité maximale)
    DIRECT = "direct"  # Clés chargées directement (fallback)
    NONE = "none"  # Aucune authentification configurée


class SmartSSHManager:
    """
    Gestionnaire SSH intelligent avec fallback.

    Ordre de préférence:
    1. SSH Agent si disponible (sécurité maximale)
    2. Clés directes sinon (fallback avec warning)
    3. Erreur si aucune méthode disponible
    """

    _instance: "SmartSSHManager | None" = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._read_connections: dict[str, SSHClientConnection] = {}
        self._exec_connections: dict[str, SSHClientConnection] = {}

        # Détection méthode d'authentification
        self._auth_mode = self._detect_auth_mode()

        # Charger clés directes si fallback nécessaire
        self._reader_key = None
        self._exec_key = None
        if self._auth_mode == SSHAuthMode.DIRECT:
            self._reader_key = self._load_key(CONFIG.ssh_key_path)
            self._exec_key = self._load_key(CONFIG.pra_key_path)

        # Audit de la configuration détectée
        self._log_auth_mode()

        self._initialized = True

    def _detect_auth_mode(self) -> SSHAuthMode:
        """
        Détecter la meilleure méthode d'authentification disponible.

        Retourne:
            AGENT: Si SSH Agent disponible et préféré
            DIRECT: Si clés disponibles mais pas d'agent
            NONE: Aucune méthode disponible (erreur)
        """
        # Forcer un mode via config
        if hasattr(CONFIG, "force_auth_mode"):
            return SSHAuthMode(CONFIG.force_auth_mode)

        # Préférer agent si disponible
        if self._check_agent():
            return SSHAuthMode.AGENT

        # Fallback: clés directes
        if CONFIG.ssh_key_path and CONFIG.pra_key_path:
            if Path(CONFIG.ssh_key_path).exists() and Path(CONFIG.pra_key_path).exists():
                return SSHAuthMode.DIRECT

        # Aucune méthode disponible
        return SSHAuthMode.NONE

    def _check_agent(self) -> bool:
        """Vérifier que SSH Agent est accessible."""
        # Désactiver agent si explicitement demandé
        if hasattr(CONFIG, "disable_ssh_agent") and CONFIG.disable_ssh_agent:
            return False

        # Windows
        if os.name == "nt":
            # OpenSSH Agent via SSH_AUTH_SOCK
            if os.environ.get("SSH_AUTH_SOCK"):
                return True

            # Pageant
            try:
                import win32api

                hwnd = win32api.FindWindow("Pageant", "Pageant")
                return hwnd != 0
            except ImportError:
                pass

            return False

        # Linux/Mac: SSH_AUTH_SOCK
        auth_sock = os.environ.get("SSH_AUTH_SOCK")
        return auth_sock is not None and Path(auth_sock).exists()

    def _load_key(self, key_path: Path | None) -> str | None:
        """Charger clé SSH (fallback uniquement)."""
        if not key_path:
            return None

        try:
            with open(key_path, "r") as f:
                return f.read()
        except Exception as e:
            audit.log_event(
                EventType.SECURITY_VIOLATION,
                Status.FAILURE,
                {
                    "error": "key_load_failed",
                    "path": str(key_path),
                    "exception": str(e),
                },
                level=LogLevel.ERROR,
            )
            return None

    def _log_auth_mode(self):
        """Auditer la méthode d'authentification détectée."""
        if self._auth_mode == SSHAuthMode.AGENT:
            # OK: sécurité maximale
            audit.log_event(
                EventType.TOOL_CALL,
                Status.SUCCESS,
                {
                    "component": "smart_ssh_manager",
                    "auth_mode": "SSH_AGENT",
                    "security_level": "MAXIMUM",
                    "message": "✅ Using SSH Agent (private keys never in memory)",
                },
                level=LogLevel.INFO,
            )

        elif self._auth_mode == SSHAuthMode.DIRECT:
            # WARNING: fallback moins sécurisé
            audit.log_event(
                EventType.SECURITY_VIOLATION,
                Status.PENDING,
                {
                    "component": "smart_ssh_manager",
                    "auth_mode": "DIRECT_KEYS",
                    "security_level": "REDUCED",
                    "warning": "⚠️  SSH Agent not available, using direct keys (less secure)",
                    "recommendation": "Start SSH Agent: 'Start-Service ssh-agent' (Windows) or 'eval $(ssh-agent)' (Linux)",
                    "impact": "Private keys will be loaded in process memory",
                },
                level=LogLevel.WARNING,
            )

        else:
            # ERROR: aucune méthode
            audit.log_event(
                EventType.SECURITY_VIOLATION,
                Status.FAILURE,
                {
                    "component": "smart_ssh_manager",
                    "auth_mode": "NONE",
                    "error": "❌ No SSH authentication method available",
                    "required": "Either start SSH Agent or configure SSH_KEY_PATH",
                },
                level=LogLevel.CRITICAL,
            )
            raise SSHConnectionError(
                "No SSH authentication method available. "
                "Please either:\n"
                "1. Start SSH Agent and load keys: ssh-add /path/to/key\n"
                "2. Configure LINUX_MCP_SSH_KEY_PATH in .env"
            )

    def get_auth_mode(self) -> SSHAuthMode:
        """Retourner le mode d'authentification actuel."""
        return self._auth_mode

    async def get_read_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """Get read-only SSH connection (diagnostics)."""
        username = username or CONFIG.user
        key = f"{username}@{host}"

        async with self._lock:
            # Reuse existing
            if key in self._read_connections:
                conn = self._read_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection
            try:
                if self._auth_mode == SSHAuthMode.AGENT:
                    # Via SSH Agent (préféré)
                    conn = await asyncssh.connect(
                        host=host,
                        username=username,
                        agent_path=os.environ.get("SSH_AUTH_SOCK"),
                        client_keys=None,  # Agent only
                        known_hosts=None,
                        connect_timeout=CONFIG.ssh_connection_timeout,
                        keepalive_interval=CONFIG.ssh_keepalive_interval,
                    )

                elif self._auth_mode == SSHAuthMode.DIRECT:
                    # Fallback: clés directes
                    conn = await asyncssh.connect(
                        host=host,
                        username=username,
                        client_keys=[self._reader_key] if self._reader_key else None,
                        passphrase=CONFIG.key_passphrase,
                        known_hosts=None,
                        connect_timeout=CONFIG.ssh_connection_timeout,
                        keepalive_interval=CONFIG.ssh_keepalive_interval,
                    )

                else:
                    raise SSHConnectionError("No authentication method available")

                self._read_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except asyncssh.misc.ChannelOpenError as e:
                if "agent" in str(e).lower() and self._auth_mode == SSHAuthMode.AGENT:
                    # Agent configuré mais clé manquante
                    audit.log_event(
                        EventType.SECURITY_VIOLATION,
                        Status.FAILURE,
                        {
                            "error": "ssh_agent_key_missing",
                            "host": host,
                            "username": username,
                            "solution": f"Load key with: ssh-add {CONFIG.ssh_key_path or '/path/to/mcp-reader.key'}",
                        },
                        level=LogLevel.ERROR,
                    )
                    raise SSHConnectionError(
                        f"SSH Agent active but mcp-reader key not loaded.\n"
                        f"Fix: ssh-add {CONFIG.ssh_key_path or '/path/to/mcp-reader.key'}"
                    )
                raise

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host}: {e}")

    async def get_exec_connection(
        self, host: str, username: str | None = None
    ) -> SSHClientConnection:
        """Get exec SSH connection (PRA actions)."""
        username = username or CONFIG.pra_user
        key = f"{username}@{host}"

        async with self._lock:
            # Reuse existing
            if key in self._exec_connections:
                conn = self._exec_connections[key]
                if not conn.is_closed():
                    log_ssh_connect(host, username, Status.SUCCESS, reused=True)
                    return conn

            # Create new connection
            try:
                if self._auth_mode == SSHAuthMode.AGENT:
                    conn = await asyncssh.connect(
                        host=host,
                        username=username,
                        agent_path=os.environ.get("SSH_AUTH_SOCK"),
                        client_keys=None,
                        known_hosts=None,
                        connect_timeout=CONFIG.ssh_connection_timeout,
                        keepalive_interval=CONFIG.ssh_keepalive_interval,
                    )

                elif self._auth_mode == SSHAuthMode.DIRECT:
                    conn = await asyncssh.connect(
                        host=host,
                        username=username,
                        client_keys=[self._exec_key] if self._exec_key else None,
                        passphrase=CONFIG.pra_key_passphrase,
                        known_hosts=None,
                        connect_timeout=CONFIG.ssh_connection_timeout,
                        keepalive_interval=CONFIG.ssh_keepalive_interval,
                    )

                else:
                    raise SSHConnectionError("No authentication method available")

                self._exec_connections[key] = conn
                log_ssh_connect(host, username, Status.SUCCESS, reused=False)
                return conn

            except asyncssh.misc.ChannelOpenError as e:
                if "agent" in str(e).lower() and self._auth_mode == SSHAuthMode.AGENT:
                    audit.log_event(
                        EventType.SECURITY_VIOLATION,
                        Status.FAILURE,
                        {
                            "error": "ssh_agent_pra_key_missing",
                            "host": host,
                            "username": username,
                            "solution": f"Load PRA key with: ssh-add {CONFIG.pra_key_path or '/path/to/pra-exec.key'}",
                        },
                        level=LogLevel.ERROR,
                    )
                    raise SSHConnectionError(
                        f"SSH Agent active but pra-exec key not loaded.\n"
                        f"Fix: ssh-add {CONFIG.pra_key_path or '/path/to/pra-exec.key'}"
                    )
                raise

            except Exception as e:
                log_ssh_connect(host, username, Status.FAILURE, error=str(e))
                raise SSHConnectionError(f"Failed to connect to {host} for PRA: {e}")

    async def execute_read_command(
        self, host: str, command: list[str], username: str | None = None
    ) -> tuple[int, str, str]:
        """Execute read-only command."""
        username = username or CONFIG.user

        if not CONFIG.is_host_allowed(host):
            audit.log_event(
                EventType.SECURITY_VIOLATION,
                Status.DENIED,
                {"error": "host_not_allowed", "host": host, "command": " ".join(command)},
                level=LogLevel.WARNING,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_read_connection(host, username)

        try:
            result = await conn.run(" ".join(command), check=False)
            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return returncode, stdout, stderr

        except Exception as e:
            raise SSHConnectionError(f"Command execution failed on {host}: {e}")

    async def execute_pra_command(
        self, host: str, action: str, username: str | None = None
    ) -> tuple[int, str, str]:
        """Execute PRA action."""
        username = username or CONFIG.pra_user

        if not CONFIG.is_host_allowed(host):
            audit.log_event(
                EventType.SECURITY_VIOLATION,
                Status.DENIED,
                {"error": "host_not_allowed_pra", "host": host, "action": action},
                level=LogLevel.WARNING,
            )
            raise SSHConnectionError(f"Host {host} not in allowed list")

        conn = await self.get_exec_connection(host, username)

        try:
            result = await conn.run(action, check=False)
            returncode = result.exit_status or 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return returncode, stdout, stderr

        except Exception as e:
            raise SSHConnectionError(f"PRA action '{action}' failed on {host}: {e}")

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


class SSHConnectionError(Exception):
    """SSH connection error."""

    pass


# Global singleton
_smart_manager: SmartSSHManager | None = None


def get_smart_ssh_manager() -> SmartSSHManager:
    """Get smart SSH manager singleton."""
    global _smart_manager
    if _smart_manager is None:
        _smart_manager = SmartSSHManager()
    return _smart_manager


async def execute_command(
    command: list[str],
    host: str | None = None,
    username: str | None = None,
) -> tuple[int, str, str]:
    """Execute command (auto-detect best auth method)."""
    if host is None:
        # Local
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
        # Remote
        manager = get_smart_ssh_manager()
        return await manager.execute_read_command(host, command, username)


async def execute_pra_action(
    action: str,
    host: str,
    username: str | None = None,
) -> tuple[int, str, str]:
    """Execute PRA action (auto-detect best auth method)."""
    manager = get_smart_ssh_manager()
    return await manager.execute_pra_command(host, action, username)


def get_current_auth_mode() -> SSHAuthMode:
    """Obtenir le mode d'authentification actuel."""
    manager = get_smart_ssh_manager()
    return manager.get_auth_mode()
