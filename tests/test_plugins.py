"""Tests for plugin system."""

import pytest

from mcp_linux_infra.analysis.plugins import (
    CommandPlugin,
    CommandSpec,
    PluginRegistry,
    get_plugin_registry,
)
from mcp_linux_infra.analysis.plugins.catalog import (
    MonitoringPlugin,
    NetworkPlugin,
    FilesystemPlugin,
    SystemdPlugin,
    ContainersPlugin,
)
from mcp_linux_infra.analysis.command_analysis import RiskLevel
from mcp_linux_infra.authorization.models import AuthLevel


def test_plugin_registry_singleton():
    """Test that get_plugin_registry returns singleton."""
    registry1 = get_plugin_registry()
    registry2 = get_plugin_registry()

    assert registry1 is registry2


def test_plugin_auto_discovery():
    """Test that builtin plugins are auto-discovered."""
    registry = get_plugin_registry()

    # Should have loaded all builtin plugins
    plugins = registry.list_plugins()
    assert len(plugins) >= 5  # At least our 5 builtin plugins

    assert "monitoring" in plugins
    assert "network" in plugins
    assert "filesystem" in plugins
    assert "systemd" in plugins
    assert "containers" in plugins


def test_monitoring_plugin():
    """Test monitoring plugin commands."""
    plugin = MonitoringPlugin()

    assert plugin.name == "monitoring"
    assert plugin.category == "monitoring"
    assert len(plugin.commands) > 0

    # Check htop command
    assert "htop" in plugin.commands
    htop_spec = plugin.commands["htop"]
    assert htop_spec.risk == RiskLevel.LOW
    assert htop_spec.level == AuthLevel.AUTO
    assert htop_spec.ssh_user == "mcp-reader"


def test_network_plugin():
    """Test network plugin commands."""
    plugin = NetworkPlugin()

    assert plugin.name == "network"
    assert "ping" in plugin.commands
    assert "curl" in plugin.commands

    ping_spec = plugin.commands["ping"]
    assert ping_spec.risk == RiskLevel.LOW
    assert ping_spec.level == AuthLevel.AUTO


def test_filesystem_plugin():
    """Test filesystem plugin commands."""
    plugin = FilesystemPlugin()

    assert plugin.name == "filesystem"
    assert "ls" in plugin.commands
    assert "grep" in plugin.commands
    assert "cat" in plugin.commands

    ls_spec = plugin.commands["ls"]
    assert ls_spec.risk == RiskLevel.LOW


def test_systemd_plugin():
    """Test systemd plugin commands."""
    plugin = SystemdPlugin()

    assert plugin.name == "systemd"
    assert "systemctl status" in plugin.commands
    assert "systemctl restart" in plugin.commands
    assert "journalctl" in plugin.commands

    # Status should be AUTO
    status_spec = plugin.commands["systemctl status"]
    assert status_spec.level == AuthLevel.AUTO

    # Restart should be MANUAL
    restart_spec = plugin.commands["systemctl restart"]
    assert restart_spec.level == AuthLevel.MANUAL


def test_containers_plugin():
    """Test containers plugin commands."""
    plugin = ContainersPlugin()

    assert plugin.name == "containers"
    assert "podman ps" in plugin.commands
    assert "podman restart" in plugin.commands
    assert "docker ps" in plugin.commands

    # ps should be AUTO
    ps_spec = plugin.commands["podman ps"]
    assert ps_spec.level == AuthLevel.AUTO

    # restart should be MANUAL
    restart_spec = plugin.commands["podman restart"]
    assert restart_spec.level == AuthLevel.MANUAL


def test_command_spec_matching():
    """Test CommandSpec pattern matching."""
    spec = CommandSpec(
        pattern=r'^htop(\s+.*)?$',
        risk=RiskLevel.LOW,
        level=AuthLevel.AUTO,
        ssh_user='mcp-reader',
        description='Test',
        rationale='Test'
    )

    assert spec.matches("htop")
    assert spec.matches("htop -u www-data")
    assert not spec.matches("iotop")


def test_plugin_get_command_spec():
    """Test plugin.get_command_spec()."""
    plugin = MonitoringPlugin()

    # Exact match
    spec = plugin.get_command_spec("htop")
    assert spec is not None
    assert spec.description == "Interactive process viewer"

    # With flags
    spec = plugin.get_command_spec("htop -u alice")
    assert spec is not None

    # No match
    spec = plugin.get_command_spec("unknown-command")
    assert spec is None


def test_registry_find_command_spec():
    """Test registry.find_command_spec()."""
    registry = get_plugin_registry()

    # Find htop
    result = registry.find_command_spec("htop")
    assert result is not None
    plugin, spec = result
    assert plugin.name == "monitoring"
    assert spec.description == "Interactive process viewer"

    # Find ping
    result = registry.find_command_spec("ping google.com")
    assert result is not None
    plugin, spec = result
    assert plugin.name == "network"

    # Unknown command
    result = registry.find_command_spec("totally-unknown-command-xyz")
    assert result is None


def test_registry_search_commands():
    """Test registry.search_commands()."""
    registry = get_plugin_registry()

    # Search for "process"
    results = registry.search_commands("process")
    assert len(results) > 0

    # Should find htop, top, etc.
    command_names = [cmd_name for cmd_name, _, _ in results]
    assert "htop" in command_names or "top" in command_names

    # Search for "network"
    results = registry.search_commands("network")
    assert len(results) > 0


def test_registry_get_commands_by_category():
    """Test getting commands by category."""
    registry = get_plugin_registry()

    monitoring_cmds = registry.get_commands_by_category("monitoring")
    assert len(monitoring_cmds) > 0
    assert "htop" in monitoring_cmds

    network_cmds = registry.get_commands_by_category("network")
    assert len(network_cmds) > 0
    assert "ping" in network_cmds


def test_registry_get_all_categories():
    """Test getting all categories."""
    registry = get_plugin_registry()

    categories = registry.get_all_categories()
    assert "monitoring" in categories
    assert "network" in categories
    assert "filesystem" in categories


def test_plugin_get_usage_guide():
    """Test plugin usage guide generation."""
    plugin = MonitoringPlugin()

    guide = plugin.get_usage_guide()
    assert "monitoring" in guide.lower()
    assert "htop" in guide
    assert len(guide) > 100  # Should be substantial


def test_plugin_get_summary():
    """Test plugin summary."""
    plugin = MonitoringPlugin()

    summary = plugin.get_summary()
    assert summary['name'] == "monitoring"
    assert summary['category'] == "monitoring"
    assert summary['command_count'] > 0
    assert 'commands' in summary


def test_registry_get_summary():
    """Test registry summary."""
    registry = get_plugin_registry()

    summary = registry.get_summary()
    assert summary['total_plugins'] >= 5
    assert summary['total_commands'] > 0
    assert 'plugins' in summary
    assert 'category_breakdown' in summary
