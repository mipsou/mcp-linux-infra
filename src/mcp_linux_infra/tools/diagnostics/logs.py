"""Diagnostic tools: Log analysis (read-only)."""

from ...connection import execute_command


async def get_journal_logs(
    lines: int = 100,
    priority: str | None = None,
    since: str | None = None,
    unit: str | None = None,
    host: str | None = None,
) -> str:
    """
    Get systemd journal logs with filters.

    **Read-only operation** via SSH mcp-reader.

    Args:
        lines: Number of log lines to retrieve
        priority: Filter by priority level
        since: Time filter (relative or absolute)
        unit: Filter by systemd unit
        host: Target host
    """
    cmd = ["journalctl", "-n", str(lines), "--no-pager"]

    if priority:
        cmd.extend(["-p", priority])

    if since:
        cmd.extend(["--since", since])

    if unit:
        cmd.extend(["-u", unit])

    returncode, stdout, stderr = await execute_command(cmd, host)

    if returncode != 0:
        return f"Error reading journal logs: {stderr}"

    filters = []
    if priority:
        filters.append(f"priority={priority}")
    if since:
        filters.append(f"since={since}")
    if unit:
        filters.append(f"unit={unit}")

    filter_str = f" ({', '.join(filters)})" if filters else ""

    return f"""## Journal Logs{filter_str}

{stdout}
"""


async def read_log_file(
    path: str,
    lines: int = 100,
    host: str | None = None,
) -> str:
    """
    Read a specific log file.

    **Read-only operation** via SSH mcp-reader.

    Note: Log path must be whitelisted in CONFIG.allowed_log_paths for security.

    Args:
        path: Path to log file (e.g., /var/log/unbound/unbound.log)
        lines: Number of lines to read from end
        host: Target host
    """
    returncode, stdout, stderr = await execute_command(
        ["tail", "-n", str(lines), path], host
    )

    if returncode != 0:
        return f"Error reading log file {path}: {stderr}"

    return f"""## Log File: {path} (last {lines} lines)

{stdout}
"""


async def search_logs(
    pattern: str,
    log_path: str | None = None,
    lines: int = 50,
    context: int = 2,
    host: str | None = None,
) -> str:
    """
    Search for pattern in logs.

    **Read-only operation** via SSH mcp-reader.

    Args:
        pattern: Regex pattern to search
        log_path: Log file path (None for journal)
        lines: Max number of matching lines
        context: Lines of context around match
        host: Target host
    """
    if log_path:
        # Search in file
        cmd = ["grep", "-E", "-n", "-i", f"-C{context}", pattern, log_path]
        returncode, stdout, stderr = await execute_command(cmd, host)

        if returncode == 0:
            # grep found matches
            return f"""## Search Results in {log_path}

Pattern: `{pattern}`
Context: ±{context} lines

{stdout}
"""
        elif returncode == 1:
            # No matches found
            return f"No matches found for pattern '{pattern}' in {log_path}"
        else:
            # Error
            return f"Error searching {log_path}: {stderr}"

    else:
        # Search in journal
        cmd = ["journalctl", "-g", pattern, "-n", str(lines), "--no-pager"]
        returncode, stdout, stderr = await execute_command(cmd, host)

        if returncode != 0:
            return f"Error searching journal: {stderr}"

        return f"""## Journal Search Results

Pattern: `{pattern}`
Max results: {lines}

{stdout}
"""


async def analyze_errors(
    service: str | None = None,
    since: str = "1h",
    host: str | None = None,
) -> str:
    """
    Analyze error logs for a service or system-wide.

    **Read-only operation** via SSH mcp-reader.

    Returns summary of errors by priority and count.

    Args:
        service: Service name (None for system-wide)
        since: Time window (default: 1h)
        host: Target host
    """
    cmd = ["journalctl", "-p", "err", "--since", since, "--no-pager"]

    if service:
        if not service.endswith(".service"):
            service = f"{service}.service"
        cmd.extend(["-u", service])

    returncode, stdout, stderr = await execute_command(cmd, host)

    if returncode != 0:
        return f"Error analyzing errors: {stderr}"

    # Count lines
    error_lines = stdout.strip().split("\n")
    error_count = len([line for line in error_lines if line.strip()])

    scope = f"service {service}" if service else "system-wide"

    return f"""## Error Analysis ({scope})

**Time Window:** {since}
**Total Errors:** {error_count}

### Recent Errors
{stdout if error_count > 0 else "No errors found in this time window."}
"""
