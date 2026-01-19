"""Tests for auto-learning system."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from mcp_linux_infra.analysis.auto_learning import (
    AutoLearningEngine,
    CommandStats,
)
from mcp_linux_infra.analysis.command_analysis import RiskLevel


@pytest.fixture
def temp_stats_file():
    """Create a temporary stats file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def learning_engine(temp_stats_file):
    """Create a learning engine with temp file."""
    return AutoLearningEngine(stats_file=temp_stats_file)


def test_record_blocked_command(learning_engine):
    """Test recording a blocked command."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")

    stats = learning_engine.get_command_stats("htop")
    assert stats is not None
    assert stats.command == "htop"
    assert stats.count == 1
    assert "alice" in stats.users
    assert "server1" in stats.hosts


def test_record_multiple_blocks(learning_engine):
    """Test recording multiple blocks of same command."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")
    learning_engine.record_blocked_command("htop", user="bob", host="server2")
    learning_engine.record_blocked_command("htop", user="alice", host="server1")

    stats = learning_engine.get_command_stats("htop")
    assert stats.count == 3
    assert set(stats.users) == {"alice", "bob"}
    assert set(stats.hosts) == {"server1", "server2"}


def test_get_all_stats(learning_engine):
    """Test getting all stats."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")
    learning_engine.record_blocked_command("iotop", user="bob", host="server2")

    all_stats = learning_engine.get_all_stats()
    assert len(all_stats) == 2
    commands = {s.command for s in all_stats}
    assert commands == {"htop", "iotop"}


def test_get_learning_suggestions_min_count(learning_engine):
    """Test that suggestions respect min_count."""
    # Record below threshold
    for _ in range(3):
        learning_engine.record_blocked_command("htop", user="alice", host="server1")

    suggestions = learning_engine.get_learning_suggestions(min_count=5)
    assert len(suggestions) == 0

    # Record above threshold
    for _ in range(2):
        learning_engine.record_blocked_command("htop", user="alice", host="server1")

    suggestions = learning_engine.get_learning_suggestions(min_count=5)
    assert len(suggestions) == 1
    assert suggestions[0]['command'] == "htop"


def test_get_learning_suggestions_risk_filter(learning_engine):
    """Test that suggestions filter by risk level."""
    # Record dangerous command
    for _ in range(10):
        learning_engine.record_blocked_command(
            "rm -rf /var/log",
            user="alice",
            host="server1"
        )

    # Should not suggest dangerous commands
    suggestions = learning_engine.get_learning_suggestions(
        min_count=5,
        min_age_hours=0,  # Ignore age for test
        max_risk=RiskLevel.LOW
    )

    # Should be empty or not contain dangerous command
    dangerous_suggestions = [s for s in suggestions if 'rm -rf' in s['command']]
    assert len(dangerous_suggestions) == 0


def test_get_top_blocked_commands(learning_engine):
    """Test getting top blocked commands."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")
    for _ in range(5):
        learning_engine.record_blocked_command("iotop", user="bob", host="server2")
    for _ in range(10):
        learning_engine.record_blocked_command("top", user="charlie", host="server3")

    top = learning_engine.get_top_blocked_commands(limit=2)
    assert len(top) == 2
    assert top[0].command == "top"
    assert top[0].count == 10
    assert top[1].command == "iotop"
    assert top[1].count == 5


def test_clear_stats(learning_engine):
    """Test clearing stats."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")
    learning_engine.record_blocked_command("iotop", user="bob", host="server2")

    # Clear specific command
    learning_engine.clear_stats("htop")
    assert learning_engine.get_command_stats("htop") is None
    assert learning_engine.get_command_stats("iotop") is not None

    # Clear all
    learning_engine.clear_stats()
    assert len(learning_engine.get_all_stats()) == 0


def test_get_stats_summary(learning_engine):
    """Test getting stats summary."""
    learning_engine.record_blocked_command("htop", user="alice", host="server1")
    learning_engine.record_blocked_command("rm -rf /", user="bob", host="server2")
    learning_engine.record_blocked_command("htop", user="alice", host="server1")

    summary = learning_engine.get_stats_summary()
    assert summary['total_unique_commands'] == 2
    assert summary['total_block_attempts'] == 3
    assert 'risk_breakdown' in summary
    assert 'category_breakdown' in summary


def test_persistence(temp_stats_file):
    """Test that stats persist across engine instances."""
    # Create engine and record
    engine1 = AutoLearningEngine(stats_file=temp_stats_file)
    engine1.record_blocked_command("htop", user="alice", host="server1")

    # Create new engine with same file
    engine2 = AutoLearningEngine(stats_file=temp_stats_file)
    stats = engine2.get_command_stats("htop")

    assert stats is not None
    assert stats.command == "htop"
    assert stats.count == 1


def test_suggestions_sorted_by_count(learning_engine):
    """Test that suggestions are sorted by count."""
    for _ in range(3):
        learning_engine.record_blocked_command("htop", user="alice", host="server1")
    for _ in range(7):
        learning_engine.record_blocked_command("iotop", user="bob", host="server2")
    for _ in range(5):
        learning_engine.record_blocked_command("top", user="charlie", host="server3")

    suggestions = learning_engine.get_learning_suggestions(
        min_count=3,
        min_age_hours=0
    )

    # Should be sorted by count descending
    assert suggestions[0]['command'] == "iotop"
    assert suggestions[0]['count'] == 7
    assert suggestions[1]['command'] == "top"
    assert suggestions[1]['count'] == 5
    assert suggestions[2]['command'] == "htop"
    assert suggestions[2]['count'] == 3
