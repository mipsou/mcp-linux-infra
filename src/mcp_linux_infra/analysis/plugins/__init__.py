"""Plugin system for command families."""

from .base import CommandPlugin, CommandSpec
from .registry import PluginRegistry, get_plugin_registry

__all__ = [
    "CommandPlugin",
    "CommandSpec",
    "PluginRegistry",
    "get_plugin_registry",
]
