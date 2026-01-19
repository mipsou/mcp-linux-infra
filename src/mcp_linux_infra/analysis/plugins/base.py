"""Base classes for command plugins."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List
import re

from ..command_analysis import RiskLevel
from ...authorization.models import AuthLevel


@dataclass
class CommandSpec:
    """Specification for a command in a plugin."""

    pattern: str
    risk: RiskLevel
    level: AuthLevel
    ssh_user: str
    description: str
    rationale: str
    examples: Optional[List[str]] = None
    flags: Optional[List[str]] = None  # Common flags

    def matches(self, command: str) -> bool:
        """Check if command matches this spec."""
        return bool(re.match(self.pattern, command))

    def to_dict(self) -> dict:
        """Convert to dictionary for analysis."""
        return {
            'pattern': self.pattern,
            'risk': self.risk.value,
            'level': self.level.value,
            'ssh_user': self.ssh_user,
            'description': self.description,
            'rationale': self.rationale,
            'examples': self.examples or [],
            'flags': self.flags or [],
        }


class CommandPlugin(ABC):
    """
    Base class for command family plugins.

    Each plugin represents a family of related commands
    (e.g., monitoring, network, filesystem).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name (unique identifier)."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Command category (monitoring, network, etc.)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass

    @property
    @abstractmethod
    def commands(self) -> Dict[str, CommandSpec]:
        """
        Dictionary of commands managed by this plugin.

        Key: command name (e.g., 'htop')
        Value: CommandSpec
        """
        pass

    def get_command_spec(self, command: str) -> Optional[CommandSpec]:
        """
        Get command spec for a given command string.

        Args:
            command: Full command string

        Returns:
            CommandSpec if matched, None otherwise
        """
        # Try exact command name match first
        base_cmd = command.split()[0] if command else ""
        if base_cmd in self.commands:
            spec = self.commands[base_cmd]
            if spec.matches(command):
                return spec

        # Try pattern matching all commands
        for cmd_name, spec in self.commands.items():
            if spec.matches(command):
                return spec

        return None

    def list_commands(self) -> List[str]:
        """List all command names in this plugin."""
        return list(self.commands.keys())

    def get_summary(self) -> dict:
        """Get summary of this plugin."""
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'command_count': len(self.commands),
            'commands': {
                name: spec.to_dict()
                for name, spec in self.commands.items()
            }
        }

    def get_usage_guide(self) -> str:
        """
        Get formatted usage guide for this plugin.

        Returns:
            Formatted string with all commands and examples
        """
        output = f"""
{'='*70}
Plugin: {self.name}
Category: {self.category}
Description: {self.description}
{'='*70}

Commands ({len(self.commands)}):

"""
        for cmd_name, spec in self.commands.items():
            output += f"""
【{cmd_name}】
  Risk: {spec.risk.value} | Level: {spec.level.value} | User: {spec.ssh_user}
  Description: {spec.description}
  Rationale: {spec.rationale}
"""

            if spec.examples:
                output += "  Examples:\n"
                for example in spec.examples:
                    output += f"    • {example}\n"

            if spec.flags:
                output += "  Common flags:\n"
                for flag in spec.flags:
                    output += f"    • {flag}\n"

        return output
