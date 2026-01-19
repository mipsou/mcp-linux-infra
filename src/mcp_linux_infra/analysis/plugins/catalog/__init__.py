"""Catalog of builtin command plugins."""

from .monitoring import MonitoringPlugin
from .network import NetworkPlugin
from .filesystem import FilesystemPlugin
from .systemd import SystemdPlugin
from .containers import ContainersPlugin
from .posix_system import PosixSystemPlugin
from .posix_process import PosixProcessPlugin
from .posix_text import PosixTextPlugin

__all__ = [
    "MonitoringPlugin",
    "NetworkPlugin",
    "FilesystemPlugin",
    "SystemdPlugin",
    "ContainersPlugin",
    "PosixSystemPlugin",
    "PosixProcessPlugin",
    "PosixTextPlugin",
]
