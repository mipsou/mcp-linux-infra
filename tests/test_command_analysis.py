"""Tests for command analysis and auto-learning."""

import pytest
from mcp_linux_infra.analysis.command_analysis import (
    analyze_command_safety,
    assess_command_risk,
    find_similar_commands,
    RiskLevel,
)
from mcp_linux_infra.authorization.models import AuthLevel


def test_analyze_safe_command():
    """Test analysis of a known safe command."""
    analysis = analyze_command_safety("htop")

    assert analysis.risk_level == RiskLevel.LOW
    assert analysis.is_readonly is True
    assert analysis.can_auto_add is True
    assert analysis.recommended_action == "ADD_AUTO"
    assert analysis.suggested_level == AuthLevel.AUTO
    assert analysis.suggested_ssh_user == "mcp-reader"


def test_analyze_dangerous_command():
    """Test analysis of a dangerous command."""
    analysis = analyze_command_safety("rm -rf /var/log")

    assert analysis.risk_level == RiskLevel.CRITICAL
    assert analysis.is_readonly is False
    assert analysis.can_auto_add is False
    assert analysis.recommended_action == "BLOCK_PERMANENTLY"
    assert analysis.suggested_level == AuthLevel.BLOCKED


def test_analyze_medium_risk_command():
    """Test analysis of a medium risk command."""
    analysis = analyze_command_safety("systemctl restart nginx")

    assert analysis.risk_level == RiskLevel.MEDIUM
    assert analysis.is_readonly is False
    assert analysis.can_auto_add is False
    assert analysis.recommended_action == "ADD_MANUAL"
    assert analysis.suggested_level == AuthLevel.MANUAL
    assert analysis.suggested_ssh_user == "pra-runner"


def test_analyze_readonly_command():
    """Test analysis of a read-only command."""
    analysis = analyze_command_safety("systemctl status nginx")

    assert analysis.risk_level == RiskLevel.LOW
    assert analysis.is_readonly is True
    assert analysis.can_auto_add is True


def test_assess_dangerous_patterns():
    """Test dangerous pattern detection."""
    dangerous_commands = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda1",
        "fdisk /dev/sda",
        "chmod -R 777 /",
    ]

    for cmd in dangerous_commands:
        result = assess_command_risk(cmd)
        assert result['risk'] == RiskLevel.CRITICAL
        assert result['is_readonly'] is False


def test_assess_medium_risk_patterns():
    """Test medium risk pattern detection."""
    medium_commands = [
        "systemctl restart unbound",
        "podman stop my-container",
        "reboot",
        "shutdown -h now",
    ]

    for cmd in medium_commands:
        result = assess_command_risk(cmd)
        assert result['risk'] == RiskLevel.MEDIUM
        assert result['suggestion'] == AuthLevel.MANUAL


def test_assess_readonly_patterns():
    """Test read-only pattern detection."""
    readonly_commands = [
        "systemctl status nginx",
        "journalctl -u sshd",
        "podman ps",
        "df -h",
        "free -m",
    ]

    for cmd in readonly_commands:
        result = assess_command_risk(cmd)
        assert result['risk'] == RiskLevel.LOW
        assert result['is_readonly'] is True
        assert result['suggestion'] == AuthLevel.AUTO


def test_find_similar_commands():
    """Test finding similar commands."""
    # This test requires whitelist to be loaded
    # For now, just check it returns a list
    similar = find_similar_commands("systemctl status nginx")
    assert isinstance(similar, list)


def test_known_safe_commands_catalog():
    """Test that known safe commands are properly catalogued."""
    safe_commands = ['htop', 'top', 'iotop', 'netstat', 'ping', 'hostname']

    for cmd in safe_commands:
        analysis = analyze_command_safety(cmd)
        assert analysis.risk_level == RiskLevel.LOW
        assert analysis.can_auto_add is True
        assert analysis.suggested_level == AuthLevel.AUTO


def test_unknown_command():
    """Test handling of unknown command."""
    analysis = analyze_command_safety("some-unknown-binary --weird-flags")

    assert analysis.risk_level == RiskLevel.UNKNOWN
    assert analysis.recommended_action == "MANUAL_REVIEW"


def test_whitelisted_command():
    """Test that already whitelisted commands are detected."""
    # This command should match whitelist pattern
    analysis = analyze_command_safety("systemctl status unbound")

    assert analysis.recommended_action == "ALREADY_WHITELISTED"
    assert analysis.can_auto_add is False
