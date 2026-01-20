"""Remote Execution (Remote Execution) Actions avec validation humaine."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


from ...audit import EventType, Status, log_pra_action
from ...connection import execute_remote_execution


class ExecutionImpact(str, Enum):
    """Niveau d'impact d'une action Remote Execution."""

    LOW = "low"  # Ex: restart service, flush cache
    MEDIUM = "medium"  # Ex: reload config, rotate logs
    HIGH = "high"  # Ex: reboot, backup restore


class RemoteExecutionStatus(str, Enum):
    """Statut d'une action Remote Execution."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RemoteExecution:
    """Définition d'une action Remote Execution."""

    id: str
    action: str
    host: str
    impact: ExecutionImpact
    rationale: str
    status: RemoteExecutionStatus
    proposed_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None


# Registry des actions Remote Execution en attente de validation
_pending_actions: dict[str, RemoteExecution] = {}


# Définition des actions Remote Execution disponibles
REMOTE_EXECUTION_CATALOG = {
    "restart_unbound": {
        "description": "Restart Unbound DNS service",
        "impact": ExecutionImpact.LOW,
        "command": "restart_unbound",
    },
    "reload_caddy": {
        "description": "Reload Caddy reverse proxy configuration",
        "impact": ExecutionImpact.LOW,
        "command": "reload_caddy",
    },
    "flush_dns_cache": {
        "description": "Flush DNS cache (systemd-resolved)",
        "impact": ExecutionImpact.LOW,
        "command": "flush_dns_cache",
    },
    "restart_container": {
        "description": "Restart a Podman container",
        "impact": ExecutionImpact.MEDIUM,
        "command": "restart_container",  # Note: nécessite paramètre container_name
    },
    "rotate_logs": {
        "description": "Force log rotation",
        "impact": ExecutionImpact.LOW,
        "command": "rotate_logs",
    },
}


async def propose_remote_execution(
    action: str,
    host: str,
    rationale: str,
    auto_approve: bool = False,
) -> str:
    """
    Propose a remote execution for human validation.

    **This is step 1 of the Remote Execution workflow:**
    1. AI proposes action with rationale
    2. Human approves/rejects via approve_remote_execution()
    3. Action executes via execute_remote_execution()

    Args:
        action: Action name from REMOTE_EXECUTION_CATALOG
        host: Target host
        rationale: Why this action is needed
        auto_approve: Skip validation (only for LOW impact, testing)

    Returns:
        Action ID for approval/execution
    """
    # Validate action exists
    if action not in REMOTE_EXECUTION_CATALOG:
        available = ", ".join(REMOTE_EXECUTION_CATALOG.keys())
        return f"❌ Unknown remote execution '{action}'. Available: {available}"

    action_def = REMOTE_EXECUTION_CATALOG[action]

    # Create remote execution
    action_id = str(uuid.uuid4())[:8]
    pra_action = RemoteExecution(
        id=action_id,
        action=action,
        host=host,
        impact=action_def["impact"],
        rationale=rationale,
        status=RemoteExecutionStatus.PROPOSED,
        proposed_at=datetime.now(),
    )

    # Log proposal
    log_pra_action(
        action=action,
        host=host,
        event_type=EventType.PRA_PROPOSED,
        status=Status.PENDING,
        rationale=rationale,
    )

    # Auto-approve si demandé ET impact LOW
    if auto_approve and action_def["impact"] == ExecutionImpact.LOW:
        pra_action.status = RemoteExecutionStatus.APPROVED
        pra_action.approved_by = "auto"
        pra_action.approved_at = datetime.now()

        log_pra_action(
            action=action,
            host=host,
            event_type=EventType.PRA_APPROVED,
            status=Status.SUCCESS,
            approver="auto",
            rationale=rationale,
        )

        _pending_actions[action_id] = pra_action

        return f"""✅ **Remote Execution Action Auto-Approved** (LOW impact)

**Action ID:** `{action_id}`
**Action:** {action} ({action_def['description']})
**Host:** {host}
**Impact:** {action_def['impact'].value.upper()}
**Rationale:** {rationale}

**Next Step:**
Call `execute_remote_execution(action_id="{action_id}")` to execute.
"""

    # Enregistrer pour validation humaine
    _pending_actions[action_id] = pra_action

    return f"""⏳ **Remote Execution Action Proposed - Awaiting Human Approval**

**Action ID:** `{action_id}`
**Action:** {action} ({action_def['description']})
**Host:** {host}
**Impact:** {action_def['impact'].value.upper()}
**Rationale:** {rationale}

**Next Steps:**
1. Human reviews and calls `approve_remote_execution(action_id="{action_id}", approved=True)`
2. Once approved, call `execute_remote_execution(action_id="{action_id}")`
"""


async def approve_remote_execution(
    action_id: str,
    approved: bool,
    approver: str = "human",
) -> str:
    """
    Approve or reject a proposed remote execution.

    **This is step 2 of the Remote Execution workflow (human validation).**

    Args:
        action_id: Action ID from propose_remote_execution
        approved: True to approve, False to reject
        approver: Identifier of the person approving

    Returns:
        Approval status message
    """
    if action_id not in _pending_actions:
        return f"❌ Unknown action ID: {action_id}"

    pra_action = _pending_actions[action_id]

    if pra_action.status != RemoteExecutionStatus.PROPOSED:
        return f"❌ Action {action_id} is not in PROPOSED state (current: {pra_action.status.value})"

    if approved:
        pra_action.status = RemoteExecutionStatus.APPROVED
        pra_action.approved_by = approver
        pra_action.approved_at = datetime.now()

        log_pra_action(
            action=pra_action.action,
            host=pra_action.host,
            event_type=EventType.PRA_APPROVED,
            status=Status.SUCCESS,
            approver=approver,
            rationale=pra_action.rationale,
        )

        return f"""✅ **Remote Execution Action Approved**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Approved by:** {approver}

**Next Step:**
Call `execute_remote_execution(action_id="{action_id}")` to execute the action.
"""
    else:
        pra_action.status = RemoteExecutionStatus.REJECTED
        pra_action.approved_by = approver
        pra_action.approved_at = datetime.now()

        log_pra_action(
            action=pra_action.action,
            host=pra_action.host,
            event_type=EventType.PRA_REJECTED,
            status=Status.DENIED,
            approver=approver,
            rationale=pra_action.rationale,
        )

        # Cleanup
        del _pending_actions[action_id]

        return f"""❌ **Remote Execution Action Rejected**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Rejected by:** {approver}

Action will not be executed.
"""


async def execute_remote_execution(
    action_id: str,
) -> str:
    """
    Execute an approved remote execution.

    **This is step 3 of the Remote Execution workflow (execution).**

    Requires prior approval via approve_remote_execution() or auto-approval.

    Args:
        action_id: Action ID from propose_remote_execution

    Returns:
        Execution result
    """
    if action_id not in _pending_actions:
        return f"❌ Unknown action ID: {action_id}"

    pra_action = _pending_actions[action_id]

    if pra_action.status != RemoteExecutionStatus.APPROVED:
        return f"❌ Action {action_id} is not APPROVED (current: {pra_action.status.value}). Cannot execute."

    # Get action definition
    action_def = REMOTE_EXECUTION_CATALOG[pra_action.action]
    command = action_def["command"]

    # Mark as executing
    pra_action.status = RemoteExecutionStatus.EXECUTING
    pra_action.executed_at = datetime.now()

    try:
        # Execute via exec-runner SSH
        returncode, stdout, stderr = await execute_remote_execution(
            action=command,
            host=pra_action.host,
        )

        if returncode == 0:
            # Success
            pra_action.status = RemoteExecutionStatus.COMPLETED
            pra_action.result = {
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

            log_pra_action(
                action=pra_action.action,
                host=pra_action.host,
                event_type=EventType.PRA_EXECUTED,
                status=Status.SUCCESS,
                approver=pra_action.approved_by,
                rationale=pra_action.rationale,
                result=pra_action.result,
            )

            # Cleanup
            del _pending_actions[action_id]

            return f"""✅ **Remote Execution Action Executed Successfully**

**Action ID:** `{action_id}`
**Action:** {pra_action.action} ({action_def['description']})
**Host:** {pra_action.host}
**Exit Code:** {returncode}

**Output:**
```
{stdout}
```

{f"**Stderr:**\n```\n{stderr}\n```" if stderr else ""}

**Recommendation:** Verify the action result with diagnostic tools.
"""

        else:
            # Failure
            pra_action.status = RemoteExecutionStatus.FAILED
            pra_action.error = stderr or "Non-zero exit code"
            pra_action.result = {
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

            log_pra_action(
                action=pra_action.action,
                host=pra_action.host,
                event_type=EventType.PRA_FAILED,
                status=Status.FAILURE,
                approver=pra_action.approved_by,
                rationale=pra_action.rationale,
                result=pra_action.result,
                error=pra_action.error,
            )

            # Keep in registry for debugging
            return f"""❌ **Remote Execution Action Failed**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Exit Code:** {returncode}

**Error:**
```
{stderr}
```

**Output:**
```
{stdout}
```

**Recommendation:** Review logs and propose a corrective action.
"""

    except Exception as e:
        pra_action.status = RemoteExecutionStatus.FAILED
        pra_action.error = str(e)

        log_pra_action(
            action=pra_action.action,
            host=pra_action.host,
            event_type=EventType.PRA_FAILED,
            status=Status.FAILURE,
            approver=pra_action.approved_by,
            rationale=pra_action.rationale,
            error=str(e),
        )

        return f"""❌ **Remote Execution Action Execution Failed**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Error:** {e}

**Recommendation:** Check SSH connectivity and exec-runner configuration.
"""


async def list_pending_actions() -> str:
    """
    List all pending remote executions awaiting approval.

    Returns:
        Summary of pending actions
    """
    if not _pending_actions:
        return "No pending remote executions."

    lines = ["## Pending Remote Execution Actions\n"]

    for action_id, pra_action in _pending_actions.items():
        lines.append(f"### Action ID: `{action_id}`")
        lines.append(f"- **Status:** {pra_action.status.value}")
        lines.append(f"- **Action:** {pra_action.action}")
        lines.append(f"- **Host:** {pra_action.host}")
        lines.append(f"- **Impact:** {pra_action.impact.value.upper()}")
        lines.append(f"- **Rationale:** {pra_action.rationale}")
        lines.append(f"- **Proposed at:** {pra_action.proposed_at.isoformat()}")
        if pra_action.approved_by:
            lines.append(f"- **Approved by:** {pra_action.approved_by}")
        lines.append("")

    return "\n".join(lines)
