"""Diagnostic tools: Systemd services (read-only)."""

from ...connection import execute_command


async def list_services(
    host: str | None = None,
) -> str:
    """
    List all systemd services with their status.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["systemctl", "list-units", "--type=service", "--all", "--no-pager"], host
    )

    if returncode != 0:
        return f"Error listing services: {stderr}"

    return f"""## Systemd Services

{stdout}
"""


async def get_service_status(
    service_name: str,
    host: str | None = None,
) -> str:
    """
    Get detailed status of a specific systemd service.

    **Read-only operation** via SSH mcp-reader.

    Args:
        service_name: Name of the service (with or without .service suffix)
        host: Target host
    """
    # Ensure .service suffix
    if not service_name.endswith(".service"):
        service_name = f"{service_name}.service"

    returncode, stdout, stderr = await execute_command(
        ["systemctl", "status", service_name, "--no-pager", "-l"], host
    )

    # Note: systemctl status returns non-zero for inactive services
    return f"""## Service Status: {service_name}

{stdout}

{f"Stderr: {stderr}" if stderr else ""}
"""


async def get_service_logs(
    service_name: str,
    lines: int = 50,
    host: str | None = None,
) -> str:
    """
    Get recent logs for a specific systemd service via journalctl.

    **Read-only operation** via SSH mcp-reader.

    Args:
        service_name: Name of the service
        lines: Number of log lines (default: 50)
        host: Target host
    """
    # Ensure .service suffix
    if not service_name.endswith(".service"):
        service_name = f"{service_name}.service"

    returncode, stdout, stderr = await execute_command(
        ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager"], host
    )

    if returncode != 0:
        return f"Error fetching logs for {service_name}: {stderr}"

    return f"""## Recent Logs: {service_name} (last {lines} lines)

{stdout}
"""


async def check_service_health(
    service_name: str,
    host: str | None = None,
) -> str:
    """
    Comprehensive health check for a service.

    **Read-only operation** via SSH mcp-reader.

    Returns:
    - Service status (active/inactive/failed)
    - Uptime
    - Recent errors in logs
    - Memory usage
    """
    if not service_name.endswith(".service"):
        service_name = f"{service_name}.service"

    # Get status
    status_rc, status_out, _ = await execute_command(
        ["systemctl", "show", service_name, "--property=ActiveState,SubState,ExecMainPID,MemoryCurrent,LoadState"], host
    )

    # Parse status
    status_lines = status_out.split("\n")
    status_dict = dict(line.split("=", 1) for line in status_lines if "=" in line)

    active_state = status_dict.get("ActiveState", "unknown")
    sub_state = status_dict.get("SubState", "unknown")
    pid = status_dict.get("ExecMainPID", "N/A")
    memory = status_dict.get("MemoryCurrent", "N/A")
    load_state = status_dict.get("LoadState", "unknown")

    # Get recent errors
    log_rc, log_out, _ = await execute_command(
        ["journalctl", "-u", service_name, "-p", "err", "-n", "20", "--no-pager"], host
    )

    errors = log_out if log_rc == 0 else "Unable to fetch errors"

    # Format health report
    health_status = "🟢 HEALTHY" if active_state == "active" else "🔴 UNHEALTHY"

    return f"""## Health Check: {service_name}

**Status:** {health_status}

**Details:**
- Load State: {load_state}
- Active State: {active_state}
- Sub State: {sub_state}
- PID: {pid}
- Memory: {memory}

**Recent Errors (last 20):**
```
{errors}
```
"""
