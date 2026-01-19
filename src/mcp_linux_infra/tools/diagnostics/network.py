"""Diagnostic tools: Network information (read-only)."""



from ...connection import execute_command


async def get_network_interfaces(
    host: str | None = None,
) -> str:
    """
    Get network interfaces configuration.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["ip", "addr", "show"], host
    )

    if returncode != 0:
        return f"Error reading network interfaces: {stderr}"

    return f"""## Network Interfaces

{stdout}
"""


async def get_routing_table(
    host: str | None = None,
) -> str:
    """
    Get routing table.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["ip", "route", "show"], host
    )

    if returncode != 0:
        return f"Error reading routing table: {stderr}"

    return f"""## Routing Table

{stdout}
"""


async def get_listening_ports(
    host: str | None = None,
) -> str:
    """
    Get listening TCP/UDP ports with associated processes.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["ss", "-lntup"], host
    )

    if returncode != 0:
        return f"Error reading listening ports: {stderr}"

    return f"""## Listening Ports

{stdout}
"""


async def get_active_connections(
    host: str | None = None,
) -> str:
    """
    Get active network connections.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["ss", "-antup"], host
    )

    if returncode != 0:
        return f"Error reading active connections: {stderr}"

    return f"""## Active Network Connections

{stdout}
"""


async def get_dns_config(
    host: str | None = None,
) -> str:
    """
    Get DNS configuration.

    **Read-only operation** via SSH mcp-reader.
    """
    # Read resolv.conf
    resolv_rc, resolv_out, _ = await execute_command(
        ["cat", "/etc/resolv.conf"], host
    )

    # Try to get systemd-resolved status
    resolved_rc, resolved_out, _ = await execute_command(
        ["resolvectl", "status"], host
    )

    output = f"""## DNS Configuration

### /etc/resolv.conf
{resolv_out if resolv_rc == 0 else "Unable to read"}

### systemd-resolved Status
{resolved_out if resolved_rc == 0 else "systemd-resolved not available or not running"}
"""

    return output


async def test_connectivity(
    target: str,
    count: int = 4,
    host: str | None = None,
) -> str:
    """
    Test network connectivity to a target.

    **Read-only operation** via SSH mcp-reader.

    Args:
        target: Hostname or IP to ping
        count: Number of ping packets (default: 4)
        host: Source host for the ping
    """
    returncode, stdout, stderr = await execute_command(
        ["ping", "-c", str(count), "-W", "2", target], host
    )

    status = "✅ REACHABLE" if returncode == 0 else "❌ UNREACHABLE"

    return f"""## Connectivity Test: {target}

**Status:** {status}

```
{stdout}
```

{f"Errors: {stderr}" if stderr else ""}
"""
