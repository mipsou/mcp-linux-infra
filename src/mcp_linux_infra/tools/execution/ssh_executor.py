"""
SSH command execution with authorization system

Provides tools for executing SSH commands with AUTO/MANUAL/BLOCKED authorization.
"""

from typing import Optional
from dataclasses import dataclass

from ...authorization import (
    AuthorizationEngine,
    COMMAND_WHITELIST,
    AuthLevel,
)
from ...connection.smart_ssh import get_smart_ssh_manager


# Global authorization engine (initialized once)
_auth_engine: Optional[AuthorizationEngine] = None


@dataclass
class CommandResult:
    """Result of SSH command execution"""
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def get_auth_engine() -> AuthorizationEngine:
    """Get or create the global authorization engine"""
    global _auth_engine
    if _auth_engine is None:
        _auth_engine = AuthorizationEngine(COMMAND_WHITELIST)
    return _auth_engine


async def _execute_ssh_command_internal(
    host: str,
    command: str,
    ssh_user: str
) -> CommandResult:
    """
    Internal SSH command execution

    Uses SmartSSHManager's execute_read_command or execute_pra_command
    depending on the SSH user.
    """
    ssh_manager = get_smart_ssh_manager()

    # Choose execution method based on SSH user
    if ssh_user == "mcp-reader":
        # Read-only command
        returncode, stdout, stderr = await ssh_manager.execute_read_command(
            host=host,
            command=["/bin/sh", "-c", command],
            username=ssh_user
        )
    elif ssh_user == "pra-runner":
        # PRA action command
        returncode, stdout, stderr = await ssh_manager.execute_pra_command(
            host=host,
            action=command,
            username=ssh_user
        )
    else:
        raise ValueError(f"Invalid SSH user: {ssh_user}")

    return CommandResult(returncode=returncode, stdout=stdout, stderr=stderr)


async def execute_ssh_command(
    host: str,
    command: str,
    auto_approve: bool = False
) -> str:
    """
    Execute SSH command with authorization check

    Args:
        host: Target host (e.g., "coreos-11" or "192.168.1.11")
        command: Command to execute
        auto_approve: Skip approval for MANUAL commands (DANGEROUS!)

    Returns:
        Command output or approval request message

    Examples:
        # Auto-approved (read-only)
        result = await execute_ssh_command("coreos-11", "systemctl status unbound")

        # Requires approval
        result = await execute_ssh_command("coreos-11", "systemctl restart unbound")
        # Returns approval ID, then use approve_command(approval_id)

        # Force execute (skip approval - DANGEROUS)
        result = await execute_ssh_command("coreos-11", "systemctl restart unbound", auto_approve=True)
    """

    engine = get_auth_engine()

    # Check authorization
    auth = engine.check_command(host, command, user="mcp-user")

    # BLOCKED
    if auth.auth_level == AuthLevel.BLOCKED:
        # Get analysis and suggestions
        from ...analysis.command_analysis import analyze_command_safety
        analysis = analyze_command_safety(command)

        suggestions = f"""
💡 SUGGESTIONS:
"""
        if analysis.recommended_action == 'ADD_AUTO':
            suggestions += f"""
  ✅ This command appears SAFE (read-only)
  → You can analyze it with: analyze_command("{command}")
  → Or execute once via PRA: propose_pra_action(action="{command}", host="{host}")
"""
        elif analysis.recommended_action == 'BLOCK_PERMANENTLY':
            suggestions += f"""
  ⚠️  This command is DANGEROUS
  → Use Ansible playbook instead for safe execution
  → Consider safer alternatives
"""
        else:
            suggestions += f"""
  → Analyze the command: analyze_command("{command}")
  → Execute once via PRA: propose_pra_action(action="{command}", host="{host}")
"""

        return f"""❌ COMMAND BLOCKED

Command: {command}
Reason: {auth.reason}
Risk Level: {analysis.risk_level.value}
Category: {analysis.category}

This command is blocked for security reasons.
{suggestions}
"""

    # AUTO - Execute immediately
    if auth.auth_level == AuthLevel.AUTO:
        try:
            result = await _execute_ssh_command_internal(
                host=host,
                command=command,
                ssh_user=auth.ssh_user
            )
            return f"""✅ Executed (auto-approved)

Command: {command}
Host: {host}
User: {auth.ssh_user}

Output:
{result.stdout}

{f"Errors:\n{result.stderr}" if result.stderr else ""}
"""
        except Exception as e:
            return f"""❌ Execution failed

Command: {command}
Host: {host}
Error: {str(e)}
"""

    # MANUAL - Needs approval
    if auth.auth_level == AuthLevel.MANUAL:
        if auto_approve:
            # Force execute (DANGEROUS!)
            try:
                result = await ssh_manager.execute_command(
                    host=host,
                    command=command,
                    username=auth.ssh_user
                )
                return f"""⚠️ Executed (auto-approved, RISKY)

Command: {command}
Host: {host}
User: {auth.ssh_user}
WARNING: Manual approval was bypassed!

Output:
{result.stdout}

{f"Errors:\n{result.stderr}" if result.stderr else ""}
"""
            except Exception as e:
                return f"""❌ Execution failed

Command: {command}
Host: {host}
Error: {str(e)}
"""
        else:
            # Return approval request
            return f"""📋 APPROVAL REQUIRED

Command: {command}
Host: {host}
SSH User: {auth.ssh_user}
Description: {auth.rule.description}
Rationale: {auth.rule.rationale}

Approval ID: {auth.approval_id}

To execute this command, use:
  approve_command("{auth.approval_id}")

To see all pending approvals:
  list_pending_approvals()
"""


async def approve_command(approval_id: str) -> str:
    """
    Approve and execute a pending command

    Args:
        approval_id: Approval request ID from execute_ssh_command

    Returns:
        Execution result or error message

    Example:
        result = await approve_command("cmd_abc12345")
    """

    engine = get_auth_engine()

    # Get pending command
    pending = engine.approve_command(approval_id)

    if not pending:
        return f"""❌ Approval not found

Approval ID: {approval_id}

Possible reasons:
- Invalid approval ID
- Command already executed
- Approval expired

Use list_pending_approvals() to see pending approvals.
"""

    # Execute the approved command
    try:
        result = await ssh_manager.execute_command(
            host=pending.host,
            command=pending.command,
            username=pending.ssh_user
        )

        # Mark as executed
        engine.mark_executed(approval_id)

        return f"""✅ Executed (approved)

Command: {pending.command}
Host: {pending.host}
User: {pending.ssh_user}
Approved at: {pending.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Output:
{result.stdout}

{f"Errors:\n{result.stderr}" if result.stderr else ""}
"""
    except Exception as e:
        return f"""❌ Execution failed

Command: {pending.command}
Host: {pending.host}
Error: {str(e)}

The approval is still valid. You can retry with:
  approve_command("{approval_id}")
"""


async def list_pending_approvals() -> str:
    """
    List all pending command approvals

    Returns:
        List of pending approvals or message if none

    Example:
        result = await list_pending_approvals()
    """

    engine = get_auth_engine()
    pending = engine.get_all_pending()

    if not pending:
        return """📋 No pending approvals

All commands have been executed or there are no pending approval requests.
"""

    output = "📋 PENDING APPROVALS\n\n"
    output += "=" * 70 + "\n\n"

    for p in pending:
        status = "✅ APPROVED" if p.approved else "⏳ WAITING"
        output += f"""ID: {p.id}
Status: {status}
Command: {p.command}
Host: {p.host}
SSH User: {p.ssh_user}
Description: {p.rule.description}
Created: {p.created_at.strftime('%Y-%m-%d %H:%M:%S')}

To approve: approve_command("{p.id}")

{"=" * 70}

"""

    return output


async def show_command_whitelist() -> str:
    """
    Show all authorized commands and their authorization levels

    Returns:
        Formatted whitelist showing AUTO/MANUAL/BLOCKED commands

    Example:
        result = await show_command_whitelist()
    """

    engine = get_auth_engine()
    summary = engine.get_whitelist_summary()

    output = """🔐 COMMAND AUTHORIZATION WHITELIST

This whitelist defines which commands can be executed and at what level.

"""

    # AUTO commands
    output += "=" * 70 + "\n"
    output += "✅ AUTO-APPROVED (Execute Immediately)\n"
    output += "=" * 70 + "\n\n"
    output += "These commands are read-only and execute without approval:\n\n"

    for rule in summary['auto']:
        output += f"""Pattern: {rule.pattern}
SSH User: {rule.ssh_user}
Description: {rule.description}
Rationale: {rule.rationale}

"""

    # MANUAL commands
    output += "\n" + "=" * 70 + "\n"
    output += "⚠️  MANUAL APPROVAL REQUIRED\n"
    output += "=" * 70 + "\n\n"
    output += "These commands require human approval before execution:\n\n"

    for rule in summary['manual']:
        output += f"""Pattern: {rule.pattern}
SSH User: {rule.ssh_user}
Description: {rule.description}
Rationale: {rule.rationale}

"""

    # BLOCKED commands
    output += "\n" + "=" * 70 + "\n"
    output += "❌ BLOCKED (Cannot Execute)\n"
    output += "=" * 70 + "\n\n"
    output += "These commands are blocked for security:\n\n"

    for rule in summary['blocked']:
        output += f"""Pattern: {rule.pattern}
Description: {rule.description}
Rationale: {rule.rationale}

"""

    output += "\n" + "=" * 70 + "\n"
    output += f"""
Total Rules:
  - Auto-approved: {len(summary['auto'])}
  - Manual approval: {len(summary['manual'])}
  - Blocked: {len(summary['blocked'])}

Default Policy: BLOCK (commands not in whitelist are blocked)
"""

    return output
