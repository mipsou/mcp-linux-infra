"""Plugin registry for auto-discovery and management."""

from typing import Dict, List, Optional, Type
import importlib
import pkgutil
from pathlib import Path

from .base import CommandPlugin, CommandSpec


class PluginRegistry:
    """
    Central registry for command plugins with auto-discovery.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._plugins: Dict[str, CommandPlugin] = {}
        self._loaded = False

    def register(self, plugin: CommandPlugin):
        """
        Register a plugin.

        Args:
            plugin: CommandPlugin instance to register
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")

        self._plugins[plugin.name] = plugin

    def unregister(self, plugin_name: str):
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]

    def get_plugin(self, plugin_name: str) -> Optional[CommandPlugin]:
        """
        Get plugin by name.

        Args:
            plugin_name: Name of plugin

        Returns:
            CommandPlugin if found, None otherwise
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def get_all_plugins(self) -> Dict[str, CommandPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def find_command_spec(self, command: str) -> Optional[tuple[CommandPlugin, CommandSpec]]:
        """
        Find command spec across all plugins.

        Args:
            command: Command string to search for

        Returns:
            Tuple of (plugin, spec) if found, None otherwise
        """
        for plugin in self._plugins.values():
            spec = plugin.get_command_spec(command)
            if spec:
                return (plugin, spec)

        return None

    def get_commands_by_category(self, category: str) -> Dict[str, CommandSpec]:
        """
        Get all commands in a specific category.

        Args:
            category: Category name

        Returns:
            Dict of command name -> CommandSpec
        """
        commands = {}
        for plugin in self._plugins.values():
            if plugin.category == category:
                commands.update(plugin.commands)

        return commands

    def get_all_categories(self) -> List[str]:
        """Get list of all unique categories."""
        return list(set(plugin.category for plugin in self._plugins.values()))

    def search_commands(self, query: str) -> List[tuple[str, CommandPlugin, CommandSpec]]:
        """
        Search commands by name or description.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of tuples (command_name, plugin, spec)
        """
        results = []
        query_lower = query.lower()

        for plugin in self._plugins.values():
            for cmd_name, spec in plugin.commands.items():
                if (query_lower in cmd_name.lower() or
                    query_lower in spec.description.lower() or
                    query_lower in spec.rationale.lower()):
                    results.append((cmd_name, plugin, spec))

        return results

    def get_summary(self) -> dict:
        """Get summary of entire registry."""
        total_commands = sum(len(p.commands) for p in self._plugins.values())

        category_breakdown = {}
        for plugin in self._plugins.values():
            cat = plugin.category
            if cat not in category_breakdown:
                category_breakdown[cat] = 0
            category_breakdown[cat] += len(plugin.commands)

        return {
            'total_plugins': len(self._plugins),
            'total_commands': total_commands,
            'categories': self.get_all_categories(),
            'category_breakdown': category_breakdown,
            'plugins': {
                name: plugin.get_summary()
                for name, plugin in self._plugins.items()
            }
        }

    def load_builtin_plugins(self):
        """
        Auto-discover and load all builtin plugins from catalog.
        """
        if self._loaded:
            return  # Already loaded

        # Get path to catalog directory
        catalog_path = Path(__file__).parent / "catalog"

        if not catalog_path.exists():
            return

        # Import all modules in catalog
        for _, module_name, _ in pkgutil.iter_modules([str(catalog_path)]):
            try:
                # Import module
                full_module = f"mcp_linux_infra.analysis.plugins.catalog.{module_name}"
                module = importlib.import_module(full_module)

                # Find CommandPlugin subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # Check if it's a CommandPlugin subclass (but not base class)
                    if (isinstance(attr, type) and
                        issubclass(attr, CommandPlugin) and
                        attr is not CommandPlugin):

                        # Instantiate and register
                        plugin_instance = attr()
                        self.register(plugin_instance)

            except Exception as e:
                # Log but don't fail
                print(f"Warning: Failed to load plugin from {module_name}: {e}")

        self._loaded = True

    def get_usage_guide(self, plugin_name: Optional[str] = None) -> str:
        """
        Get formatted usage guide.

        Args:
            plugin_name: Specific plugin name, or None for all

        Returns:
            Formatted usage guide
        """
        if plugin_name:
            plugin = self.get_plugin(plugin_name)
            if not plugin:
                return f"Plugin '{plugin_name}' not found."
            return plugin.get_usage_guide()

        # All plugins
        output = f"""
{'='*70}
COMMAND PLUGIN REGISTRY
{'='*70}

Total Plugins: {len(self._plugins)}
Total Commands: {sum(len(p.commands) for p in self._plugins.values())}
Categories: {', '.join(self.get_all_categories())}

{'='*70}

"""
        for plugin_name in sorted(self.list_plugins()):
            plugin = self._plugins[plugin_name]
            output += plugin.get_usage_guide()
            output += "\n"

        return output


# Global singleton
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """
    Get or create the global plugin registry.

    Returns:
        PluginRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.load_builtin_plugins()

    return _registry
