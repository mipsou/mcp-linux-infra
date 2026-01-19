"""PRA (Plan de Reprise d'Activité) Actions avec validation humaine."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


from ...audit import EventType, Status, log_pra_action
from ...connection import execute_pra_action


class PRAImpact(str, Enum):
    """Niveau d'impact d'une action PRA."""

    LOW = "low"  # Ex: restart service, flush cache
    MEDIUM = "medium"  # Ex: reload config, rotate logs
    HIGH = "high"  # Ex: reboot, backup restore


class PRAActionStatus(str, Enum):
    """Statut d'une action PRA."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PRAAction:
    """Définition d'une action PRA."""

    id: str
    action: str
    host: str
    impact: PRAImpact
    rationale: str
    status: PRAActionStatus
    proposed_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None


# Registry des actions PRA en attente de validation
_pending_actions: dict[str, PRAAction] = {}


# Définition des actions PRA disponibles
PRA_ACTION_CATALOG = {
    "restart_unbound": {
        "description": "Restart Unbound DNS service",
        "impact": PRAImpact.LOW,
        "command": "restart_unbound",
    },
    "reload_caddy": {
        "description": "Reload Caddy reverse proxy configuration",
        "impact": PRAImpact.LOW,
        "command": "reload_caddy",
    },
    "flush_dns_cache": {
        "description": "Flush DNS cache (systemd-resolved)",
        "impact": PRAImpact.LOW,
        "command": "flush_dns_cache",
    },
    "restart_container": {
        "description": "Restart a Podman container",
        "impact": PRAImpact.MEDIUM,
        "command": "restart_container",  # Note: nécessite paramètre container_name
    },
    "rotate_logs": {
        "description": "Force log rotation",
        "impact": PRAImpact.LOW,
        "command": "rotate_logs",
    },
}


async def propose_pra_action(
    action: str,
    host: str,
    rationale: str,
    auto_approve: bool = False,
) -> str:
    """
    Propose a PRA action for human validation.

    **This is step 1 of the PRA workflow:**
    1. AI proposes action with rationale
    2. Human approves/rejects via approve_pra_action()
    3. Action executes via execute_pra_action()

    Args:
        action: Action name from PRA_ACTION_CATALOG
        host: Target host
        rationale: Why this action is needed
        auto_approve: Skip validation (only for LOW impact, testing)

    Returns:
        Action ID for approval/execution
    """
    # Validate action exists
    if action not in PRA_ACTION_CATALOG:
        available = ", ".join(PRA_ACTION_CATALOG.keys())
        return f"❌ Unknown PRA action '{action}'. Available: {available}"

    action_def = PRA_ACTION_CATALOG[action]

    # Create PRA action
    action_id = str(uuid.uuid4())[:8]
    pra_action = PRAAction(
        id=action_id,
        action=action,
        host=host,
        impact=action_def["impact"],
        rationale=rationale,
        status=PRAActionStatus.PROPOSED,
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
    if auto_approve and action_def["impact"] == PRAImpact.LOW:
        pra_action.status = PRAActionStatus.APPROVED
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

        return f"""✅ **PRA Action Auto-Approved** (LOW impact)

**Action ID:** `{action_id}`
**Action:** {action} ({action_def['description']})
**Host:** {host}
**Impact:** {action_def['impact'].value.upper()}
**Rationale:** {rationale}

**Next Step:**
Call `execute_pra_action(action_id="{action_id}")` to execute.
"""

    # Enregistrer pour validation humaine
    _pending_actions[action_id] = pra_action

    return f"""⏳ **PRA Action Proposed - Awaiting Human Approval**

**Action ID:** `{action_id}`
**Action:** {action} ({action_def['description']})
**Host:** {host}
**Impact:** {action_def['impact'].value.upper()}
**Rationale:** {rationale}

**Next Steps:**
1. Human reviews and calls `approve_pra_action(action_id="{action_id}", approved=True)`
2. Once approved, call `execute_pra_action(action_id="{action_id}")`
"""


async def approve_pra_action(
    action_id: str,
    approved: bool,
    approver: str = "human",
) -> str:
    """
    Approve or reject a proposed PRA action.

    **This is step 2 of the PRA workflow (human validation).**

    Args:
        action_id: Action ID from propose_pra_action
        approved: True to approve, False to reject
        approver: Identifier of the person approving

    Returns:
        Approval status message
    """
    if action_id not in _pending_actions:
        return f"❌ Unknown action ID: {action_id}"

    pra_action = _pending_actions[action_id]

    if pra_action.status != PRAActionStatus.PROPOSED:
        return f"❌ Action {action_id} is not in PROPOSED state (current: {pra_action.status.value})"

    if approved:
        pra_action.status = PRAActionStatus.APPROVED
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

        return f"""✅ **PRA Action Approved**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Approved by:** {approver}

**Next Step:**
Call `execute_pra_action(action_id="{action_id}")` to execute the action.
"""
    else:
        pra_action.status = PRAActionStatus.REJECTED
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

        return f"""❌ **PRA Action Rejected**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Rejected by:** {approver}

Action will not be executed.
"""


async def execute_pra_action(
    action_id: str,
) -> str:
    """
    Execute an approved PRA action.

    **This is step 3 of the PRA workflow (execution).**

    Requires prior approval via approve_pra_action() or auto-approval.

    Args:
        action_id: Action ID from propose_pra_action

    Returns:
        Execution result
    """
    if action_id not in _pending_actions:
        return f"❌ Unknown action ID: {action_id}"

    pra_action = _pending_actions[action_id]

    if pra_action.status != PRAActionStatus.APPROVED:
        return f"❌ Action {action_id} is not APPROVED (current: {pra_action.status.value}). Cannot execute."

    # Get action definition
    action_def = PRA_ACTION_CATALOG[pra_action.action]
    command = action_def["command"]

    # Mark as executing
    pra_action.status = PRAActionStatus.EXECUTING
    pra_action.executed_at = datetime.now()

    try:
        # Execute via pra-runner SSH
        returncode, stdout, stderr = await execute_pra_action(
            action=command,
            host=pra_action.host,
        )

        if returncode == 0:
            # Success
            pra_action.status = PRAActionStatus.COMPLETED
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

            return f"""✅ **PRA Action Executed Successfully**

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
            pra_action.status = PRAActionStatus.FAILED
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
            return f"""❌ **PRA Action Failed**

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
        pra_action.status = PRAActionStatus.FAILED
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

        return f"""❌ **PRA Action Execution Failed**

**Action ID:** `{action_id}`
**Action:** {pra_action.action}
**Host:** {pra_action.host}
**Error:** {e}

**Recommendation:** Check SSH connectivity and pra-runner configuration.
"""


async def list_pending_actions() -> str:
    """
    List all pending PRA actions awaiting approval.

    Returns:
        Summary of pending actions
    """
    if not _pending_actions:
        return "No pending PRA actions."

    lines = ["## Pending PRA Actions\n"]

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
