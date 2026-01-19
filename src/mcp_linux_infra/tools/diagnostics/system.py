"""Diagnostic tools: System information (read-only)."""



from ...connection import execute_command


async def get_system_info(
    host: str | None = None,
) -> str:
    """
    Get comprehensive system information.

    **Read-only operation** via SSH mcp-reader.

    Returns:
    - OS and distribution
    - Kernel version
    - System uptime
    - Load averages
    - Architecture
    """
    commands = [
        ("OS", ["cat", "/etc/os-release"]),
        ("Kernel", ["uname", "-a"]),
        ("Uptime", ["uptime"]),
        ("Load", ["cat", "/proc/loadavg"]),
        ("Hostname", ["hostname", "-f"]),
    ]

    output_parts = []

    for label, cmd in commands:
        returncode, stdout, stderr = await execute_command(cmd, host)

        if returncode == 0:
            output_parts.append(f"## {label}\n{stdout.strip()}\n")
        else:
            output_parts.append(f"## {label}\nError: {stderr.strip()}\n")

    return "\n".join(output_parts)


async def get_cpu_info(
    host: str | None = None,
) -> str:
    """
    Get CPU information.

    **Read-only operation** via SSH mcp-reader.

    Returns:
    - CPU model
    - Number of cores
    - CPU frequencies
    - CPU usage
    """
    returncode, stdout, stderr = await execute_command(
        ["cat", "/proc/cpuinfo"], host
    )

    if returncode != 0:
        return f"Error reading CPU info: {stderr}"

    # Parse relevant fields
    lines = stdout.split("\n")
    cpu_model = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("model name")), "Unknown")
    cpu_count = len([line for line in lines if line.startswith("processor")])

    # Get load average
    load_rc, load_out, _ = await execute_command(["cat", "/proc/loadavg"], host)
    load_avg = load_out.strip() if load_rc == 0 else "Unknown"

    return f"""## CPU Information

Model: {cpu_model}
Physical Cores: {cpu_count}
Load Average: {load_avg}

## Full Details
{stdout}
"""


async def get_memory_info(
    host: str | None = None,
) -> str:
    """
    Get memory information (RAM + Swap).

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["free", "-h"], host
    )

    if returncode != 0:
        return f"Error reading memory info: {stderr}"

    return f"""## Memory Information

{stdout}

## Detailed Meminfo
"""

    # Also get detailed meminfo
    mem_rc, mem_out, _ = await execute_command(["cat", "/proc/meminfo"], host)
    if mem_rc == 0:
        return f"{stdout}\n\n## Detailed Meminfo\n{mem_out}"

    return stdout


async def get_disk_usage(
    host: str | None = None,
) -> str:
    """
    Get disk usage information for all mount points.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["df", "-h", "-x", "tmpfs", "-x", "devtmpfs"], host
    )

    if returncode != 0:
        return f"Error reading disk usage: {stderr}"

    return f"""## Disk Usage

{stdout}
"""


async def get_block_devices(
    host: str | None = None,
) -> str:
    """
    List block devices with size and mount points.

    **Read-only operation** via SSH mcp-reader.
    """
    returncode, stdout, stderr = await execute_command(
        ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE"], host
    )

    if returncode != 0:
        return f"Error listing block devices: {stderr}"

    return f"""## Block Devices

{stdout}
"""
