"""Auto-learning system for command authorization."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

from ..config import get_settings
from .command_analysis import analyze_command_safety, RiskLevel


@dataclass
class CommandStats:
    """Statistics for a blocked command."""
    command: str
    count: int
    first_seen: str
    last_seen: str
    users: list[str]
    hosts: list[str]
    risk_level: str
    category: str


class AutoLearningEngine:
    """
    Auto-learning engine that tracks blocked commands and suggests
    additions to the whitelist.
    """

    def __init__(self, stats_file: Optional[Path] = None):
        """
        Initialize auto-learning engine.

        Args:
            stats_file: Path to stats file (default: logs/command_stats.json)
        """
        settings = get_settings()

        if stats_file is None:
            log_dir = Path(settings.log_dir) if settings.log_dir else Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            stats_file = log_dir / "command_stats.json"

        self.stats_file = stats_file
        self.stats: dict[str, dict] = self._load_stats()

    def _load_stats(self) -> dict:
        """Load stats from file."""
        if not self.stats_file.exists():
            return {}

        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_stats(self):
        """Save stats to file."""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save stats: {e}")

    def record_blocked_command(
        self,
        command: str,
        user: str = "unknown",
        host: str = "unknown"
    ):
        """
        Record a blocked command execution attempt.

        Args:
            command: The blocked command
            user: User who attempted the command
            host: Host where command was attempted
        """
        now = datetime.now().isoformat()

        if command not in self.stats:
            # New command - analyze it
            analysis = analyze_command_safety(command)

            self.stats[command] = {
                'command': command,
                'count': 0,
                'first_seen': now,
                'last_seen': now,
                'users': [],
                'hosts': [],
                'risk_level': analysis.risk_level.value,
                'category': analysis.category,
            }

        # Update stats
        stats_entry = self.stats[command]
        stats_entry['count'] += 1
        stats_entry['last_seen'] = now

        if user not in stats_entry['users']:
            stats_entry['users'].append(user)

        if host not in stats_entry['hosts']:
            stats_entry['hosts'].append(host)

        self._save_stats()

    def get_command_stats(self, command: str) -> Optional[CommandStats]:
        """
        Get statistics for a specific command.

        Args:
            command: The command to look up

        Returns:
            CommandStats if found, None otherwise
        """
        if command not in self.stats:
            return None

        data = self.stats[command]
        return CommandStats(**data)

    def get_all_stats(self) -> list[CommandStats]:
        """
        Get statistics for all tracked commands.

        Returns:
            List of CommandStats
        """
        return [CommandStats(**data) for data in self.stats.values()]

    def get_learning_suggestions(
        self,
        min_count: int = 5,
        min_age_hours: int = 24,
        max_risk: RiskLevel = RiskLevel.LOW
    ) -> list[dict]:
        """
        Get suggestions for commands that should be added to whitelist.

        Args:
            min_count: Minimum number of blocked attempts
            min_age_hours: Minimum age in hours since first seen
            max_risk: Maximum acceptable risk level

        Returns:
            List of suggestions with command details
        """
        suggestions = []
        now = datetime.now()

        for command, data in self.stats.items():
            # Check criteria
            if data['count'] < min_count:
                continue

            first_seen = datetime.fromisoformat(data['first_seen'])
            age_hours = (now - first_seen).total_seconds() / 3600

            if age_hours < min_age_hours:
                continue

            risk_level = RiskLevel(data['risk_level'])

            # Only suggest LOW risk commands by default
            if max_risk == RiskLevel.LOW and risk_level != RiskLevel.LOW:
                continue

            # Analyze command for detailed suggestion
            analysis = analyze_command_safety(command)

            suggestions.append({
                'command': command,
                'count': data['count'],
                'users': data['users'],
                'hosts': data['hosts'],
                'age_hours': int(age_hours),
                'risk_level': risk_level.value,
                'category': data['category'],
                'suggested_level': analysis.suggested_level.value if analysis.suggested_level else None,
                'suggested_ssh_user': analysis.suggested_ssh_user,
                'rationale': analysis.rationale,
                'can_auto_add': analysis.can_auto_add,
                'recommended_action': analysis.recommended_action,
            })

        # Sort by count (most requested first)
        suggestions.sort(key=lambda x: x['count'], reverse=True)

        return suggestions

    def get_top_blocked_commands(self, limit: int = 10) -> list[CommandStats]:
        """
        Get top N most frequently blocked commands.

        Args:
            limit: Number of commands to return

        Returns:
            List of CommandStats sorted by count
        """
        all_stats = self.get_all_stats()
        all_stats.sort(key=lambda x: x.count, reverse=True)
        return all_stats[:limit]

    def clear_stats(self, command: Optional[str] = None):
        """
        Clear statistics.

        Args:
            command: Specific command to clear, or None to clear all
        """
        if command:
            if command in self.stats:
                del self.stats[command]
        else:
            self.stats = {}

        self._save_stats()

    def get_stats_summary(self) -> dict:
        """
        Get summary of learning stats.

        Returns:
            Dict with summary information
        """
        total_commands = len(self.stats)
        total_blocks = sum(data['count'] for data in self.stats.values())

        risk_breakdown = defaultdict(int)
        category_breakdown = defaultdict(int)

        for data in self.stats.values():
            risk_breakdown[data['risk_level']] += 1
            category_breakdown[data['category']] += 1

        return {
            'total_unique_commands': total_commands,
            'total_block_attempts': total_blocks,
            'risk_breakdown': dict(risk_breakdown),
            'category_breakdown': dict(category_breakdown),
            'stats_file': str(self.stats_file),
        }


# Global instance
_learning_engine: Optional[AutoLearningEngine] = None


def get_learning_engine() -> AutoLearningEngine:
    """Get or create the global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = AutoLearningEngine()
    return _learning_engine


def record_blocked_command(command: str, user: str = "unknown", host: str = "unknown"):
    """
    Record a blocked command (convenience function).

    Args:
        command: The blocked command
        user: User who attempted
        host: Host where attempted
    """
    engine = get_learning_engine()
    engine.record_blocked_command(command, user, host)


def get_learning_suggestions(**kwargs) -> list[dict]:
    """
    Get learning suggestions (convenience function).

    Args:
        **kwargs: Arguments passed to AutoLearningEngine.get_learning_suggestions

    Returns:
        List of suggestions
    """
    engine = get_learning_engine()
    return engine.get_learning_suggestions(**kwargs)
